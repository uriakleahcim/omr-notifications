from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from omr_notifications.adapters import FilesystemAdapter, TimeAdapter
from omr_notifications.models import EventNormalizer
from omr_notifications.paths import RuntimePaths
from omr_notifications.persistence import ConfigManager, Journal, atomic_write_json
from omr_notifications.validation import default_config


class PersistenceAndAdapterTests(unittest.TestCase):
    def make_paths(self, root: Path) -> RuntimePaths:
        return RuntimePaths(root / "config", root / "state", root / "cache", root / "run")

    def test_invalid_candidate_falls_back_to_last_known_good(self):
        with tempfile.TemporaryDirectory() as raw:
            paths = self.make_paths(Path(raw))
            good = default_config()
            good["revision"] = 7
            atomic_write_json(paths.last_good_file, good)
            paths.config_dir.mkdir(parents=True)
            paths.config_file.write_text("{ invalid", encoding="utf-8")
            config, source = ConfigManager(paths).load_initial()
            self.assertEqual("last-known-good", source)
            self.assertEqual(7, config["revision"])

    def test_invalid_reload_keeps_active_revision(self):
        with tempfile.TemporaryDirectory() as raw:
            paths = self.make_paths(Path(raw))
            config = default_config()
            config["revision"] = 3
            atomic_write_json(paths.config_file, config)
            manager = ConfigManager(paths)
            manager.load_initial()
            paths.config_file.write_text(json.dumps({"schemaVersion": 99}), encoding="utf-8")
            self.assertFalse(manager.reload_if_changed(force=True))
            self.assertEqual(3, manager.active["revision"])
            self.assertIsNotNone(manager.rejected)

    def test_journal_is_bounded_by_records(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "events.jsonl"
            journal = Journal(path, max_records=3, max_bytes=100000)
            normalizer = EventNormalizer()
            for i in range(40):
                journal.append(normalizer.create(event_type="test.event", listener_id="x", adapter="fixture", data={"i": i}))
            journal.prune()
            records = journal.tail(10)
            self.assertEqual(3, len(records))
            self.assertEqual(39, records[-1]["event"]["data"]["i"])

    def test_time_after_fires_once_and_persists_due(self):
        state = {}
        adapter = TimeAdapter(state)
        listener = {"id": "delay", "type": "time.after", "config": {"seconds": 5}}
        self.assertEqual([], adapter.poll([listener], 100))
        self.assertEqual([], adapter.poll([listener], 104))
        emitted = adapter.poll([listener], 105)
        self.assertEqual("time.after", emitted[0].event_type)
        self.assertEqual([], adapter.poll([listener], 200))

    def test_filesystem_correlates_move_without_following_content(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            original = root / "before.txt"
            original.write_text("content", encoding="utf-8")
            listener = {
                "id": "files", "type": "filesystem.watch",
                "config": {"roots": [str(root)], "pollSeconds": 1, "recursive": False},
            }
            adapter = FilesystemAdapter()
            self.assertEqual([], adapter.poll([listener], 1))
            moved = root / "after.txt"
            original.rename(moved)
            events = adapter.poll([listener], 2)
            self.assertEqual(["filesystem.entry.moved"], [x.event_type for x in events])
            self.assertEqual(str(original), events[0].data["from"])
            self.assertNotIn("content", events[0].data)

    def test_equivalent_filesystem_listeners_share_one_snapshot(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            listeners = [
                {"id": "one", "type": "filesystem.watch", "config": {"roots": [raw], "pollSeconds": 1}},
                {"id": "two", "type": "filesystem.watch", "config": {"roots": [raw], "pollSeconds": 1}},
            ]
            adapter = FilesystemAdapter()
            adapter.poll(listeners, 1)
            self.assertEqual(1, len(adapter.snapshots))
            (root / "new.txt").write_text("x", encoding="utf-8")
            events = adapter.poll(listeners, 2)
            self.assertEqual({"one", "two"}, {event.listener_id for event in events})


if __name__ == "__main__":
    unittest.main()
