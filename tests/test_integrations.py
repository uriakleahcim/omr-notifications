from __future__ import annotations

import argparse
import json
import unittest
from unittest.mock import patch

from omr_notifications.cli import command_codex_notify
from omr_notifications.integrations import codex_completion_event
from omr_notifications.paths import RuntimePaths


class CodexIntegrationTests(unittest.TestCase):
    def test_completion_payload_is_minimized(self):
        event = codex_completion_event({
            "type": "agent-turn-complete",
            "thread-id": "thread-1",
            "turn-id": "turn-2",
            "cwd": "/home/example/Work/project",
            "input-messages": ["private prompt"],
            "last-assistant-message": "private response",
        })
        self.assertEqual("codex.agent-turn-complete", event["type"])
        self.assertEqual("project", event["data"]["project"])
        self.assertNotIn("input-messages", event["data"])
        self.assertNotIn("last-assistant-message", event["data"])

    def test_non_completion_payload_is_ignored(self):
        self.assertIsNone(codex_completion_event({"type": "something-else"}))

    @patch("omr_notifications.cli.send_request", side_effect=ConnectionError("offline"))
    def test_codex_notifier_is_best_effort_when_runtime_is_offline(self, _send):
        args = argparse.Namespace(payload=json.dumps({"type": "agent-turn-complete"}))
        paths = RuntimePaths.discover()
        self.assertEqual(0, command_codex_notify(args, paths))


if __name__ == "__main__":
    unittest.main()
