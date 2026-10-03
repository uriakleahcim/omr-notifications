from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from omr_notifications.actions import ActionDispatcher, render
from omr_notifications.models import EventNormalizer
from omr_notifications.paths import RuntimePaths
from omr_notifications.persistence import atomic_write_json
from omr_notifications.runtime import CompanionRuntime
from omr_notifications.validation import default_config, impact_for_listener


class ActionsAndRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.event = EventNormalizer().create(
            event_type="test.event", listener_id="input", adapter="fixture",
            data={"name": "literal; $(touch never)"},
        )

    def test_template_rendering_only_reads_event_fields(self):
        rendered = render("Got ${event.data.name}; ${event.data.missing}", self.event)
        self.assertEqual("Got literal; $(touch never); ", rendered)

    def test_exec_argv_is_literal(self):
        dispatcher = ActionDispatcher(timeout=2)
        result = dispatcher.dispatch({
            "id": "literal", "type": "exec.argv",
            "config": {"argv": ["printf", "%s", "${event.data.name}"]},
        }, self.event, "policy")
        self.assertEqual("success", result.status)
        self.assertEqual("literal; $(touch never)", result.output)

    @patch("omr_notifications.actions.shutil.which", return_value="/usr/bin/tool")
    def test_notification_falls_back_to_omacale_when_dbus_provider_is_absent(self, _which):
        dispatcher = ActionDispatcher()
        dispatcher._run = Mock(side_effect=[
            ("failure", "exit code 1", "GDBus.Error:org.freedesktop.DBus.Error.ServiceUnknown"),
            ("success", "", ""),
        ])
        result = dispatcher.dispatch({
            "id": "popup", "type": "notification.show",
            "config": {"title": "Hello", "body": "World", "urgency": "normal"},
        }, self.event, "policy")
        self.assertEqual("success", result.status)
        self.assertIn("Omacale", result.message)
        self.assertEqual(
            ["omarchy-shell", "omacale", "toast", "info", "Hello", "World", "notifications_active"],
            dispatcher._run.call_args_list[1].args[0],
        )

    def make_runtime(self, root: Path, config: dict) -> CompanionRuntime:
        paths = RuntimePaths(root / "config", root / "state", root / "cache", root / "run")
        atomic_write_json(paths.config_file, config)
        return CompanionRuntime(paths, dry_run=True)

    def test_ingress_is_allowlisted_and_queue_is_bounded(self):
        with tempfile.TemporaryDirectory() as raw:
            config = default_config()
            config["limits"]["queueCapacity"] = 1
            config["listeners"] = [{
                "id": "input", "type": "explicit.ingress", "enabled": True,
                "config": {"eventTypes": ["test.event"]},
            }]
            runtime = self.make_runtime(Path(raw), config)
            accepted = runtime.handle_request({"command": "emit", "event": {"type": "test.event", "listenerId": "input", "data": {}}})
            self.assertTrue(accepted["ok"])
            rejected = runtime.handle_request({"command": "emit", "event": {"type": "test.event", "listenerId": "input", "data": {}}})
            self.assertFalse(rejected["ok"])
            self.assertEqual(1, runtime.dropped)
            with self.assertRaises(ValueError):
                runtime.handle_request({"command": "emit", "event": {"type": "other.event", "listenerId": "input", "data": {}}})

    def test_unacknowledged_sensitive_listener_stays_inactive(self):
        with tempfile.TemporaryDirectory() as raw:
            config = default_config()
            listener = {
                "id": "files", "type": "filesystem.watch", "enabled": True,
                "config": {"roots": [raw], "recursive": True},
            }
            config["listeners"] = [listener]
            runtime = self.make_runtime(Path(raw) / "runtime", config)
            self.assertEqual([], runtime._active_listeners())
            config["impactAcknowledgements"] = [impact_for_listener(listener)["fingerprint"]]
            runtime = self.make_runtime(Path(raw) / "runtime2", config)
            self.assertEqual(["files"], [x["id"] for x in runtime._active_listeners()])

    def test_listener_state_action_is_idempotent_and_causal(self):
        with tempfile.TemporaryDirectory() as raw:
            config = default_config()
            config["listeners"] = [{"id": "target", "type": "explicit.ingress", "enabled": True, "config": {}}]
            runtime = self.make_runtime(Path(raw), config)
            parent = EventNormalizer().create(event_type="test.event", listener_id="target", adapter="fixture")
            self.assertTrue(runtime._set_listener("target", False, parent))
            self.assertFalse(runtime._set_listener("target", False, parent))
            derived = runtime.queue[0]
            self.assertEqual(parent.id, derived.causation_id)
            self.assertEqual(parent.correlation_id, derived.correlation_id)

    def test_command_policy_fails_closed_until_acknowledged(self):
        with tempfile.TemporaryDirectory() as raw:
            config = default_config()
            config["listeners"] = [{"id": "input", "type": "explicit.ingress", "enabled": True, "config": {}}]
            config["policies"] = [{
                "id": "command", "priority": 1, "trigger": {"types": ["test.event"]},
                "actions": [{"type": "exec.argv", "config": {"argv": ["true"]}}],
            }]
            runtime = self.make_runtime(Path(raw) / "closed", config)
            self.assertEqual([], runtime.engine.policies)
            config["impactAcknowledgements"] = ["exec.argv"]
            runtime = self.make_runtime(Path(raw) / "open", config)
            self.assertEqual(["command"], [x["id"] for x in runtime.engine.policies])

    def test_stop_event_failure_skips_later_policy(self):
        with tempfile.TemporaryDirectory() as raw:
            config = default_config()
            config["impactAcknowledgements"] = ["exec.argv"]
            config["listeners"] = [{"id": "input", "type": "explicit.ingress", "enabled": True, "config": {}}]
            config["policies"] = [
                {
                    "id": "a-fail", "priority": 2, "trigger": {"types": ["test.event"]},
                    "actions": [{"type": "exec.argv", "config": {"argv": ["/bin/false"]}}],
                    "errorStrategy": "stop-event",
                },
                {
                    "id": "b-record", "priority": 1, "trigger": {"types": ["test.event"]},
                    "actions": [{"type": "event.record", "config": {}}],
                },
            ]
            runtime = self.make_runtime(Path(raw), config)
            runtime.dispatcher.dry_run = False
            runtime.accept(EventNormalizer().create(event_type="test.event", listener_id="input", adapter="fixture"))
            runtime.process_queue()
            self.assertEqual(1, runtime.failed_actions)
            self.assertEqual([], runtime.journal.tail())

    def test_duplicate_runtime_detects_live_socket_owner(self):
        with tempfile.TemporaryDirectory() as raw:
            runtime = self.make_runtime(Path(raw), default_config())
            runtime.paths.runtime_dir.mkdir(parents=True)
            runtime.paths.socket_file.touch()
            with patch("omr_notifications.runtime.send_request", return_value={"ok": True}):
                self.assertTrue(runtime._runtime_already_running())

    def test_stale_runtime_socket_is_removed(self):
        with tempfile.TemporaryDirectory() as raw:
            runtime = self.make_runtime(Path(raw), default_config())
            runtime.paths.runtime_dir.mkdir(parents=True)
            runtime.paths.socket_file.touch()
            with patch("omr_notifications.runtime.send_request", side_effect=ConnectionError("stale")):
                self.assertFalse(runtime._runtime_already_running())
            self.assertFalse(runtime.paths.socket_file.exists())

    def test_runtime_lock_allows_only_one_owner(self):
        with tempfile.TemporaryDirectory() as raw:
            first = self.make_runtime(Path(raw), default_config())
            second = CompanionRuntime(first.paths, dry_run=True)
            self.assertTrue(first._acquire_runtime_lock())
            self.assertFalse(second._acquire_runtime_lock())
            first.lock_stream.close()


if __name__ == "__main__":
    unittest.main()
