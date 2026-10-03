from __future__ import annotations

import unittest

from omr_notifications.models import EventNormalizer
from omr_notifications.validation import ConfigError, default_config, impact_for_listener, validate_config


class ModelsAndValidationTests(unittest.TestCase):
    def test_event_is_immutable_and_sequences(self):
        normalizer = EventNormalizer(initial_sequence=4)
        event = normalizer.create(event_type="test.event", listener_id="listener", adapter="fixture", data={"nested": {"x": 1}})
        self.assertEqual(5, event.sequence)
        self.assertEqual(event.id, event.correlation_id)
        with self.assertRaises(TypeError):
            event.data["new"] = 2
        with self.assertRaises(TypeError):
            event.data["nested"]["x"] = 3

    def test_default_config_validates_and_limits_are_merged(self):
        config = default_config()
        config["limits"] = {"queueCapacity": 12}
        result = validate_config(config)
        self.assertEqual(12, result["limits"]["queueCapacity"])
        self.assertEqual(8, result["limits"]["causalDepth"])

    def test_unknown_listener_reference_is_rejected(self):
        config = default_config()
        config["policies"] = [{
            "id": "bad", "priority": 0,
            "trigger": {"types": ["test.event"], "listenerIds": ["missing"]},
            "actions": [{"type": "event.record", "config": {}}],
        }]
        with self.assertRaises(ConfigError) as raised:
            validate_config(config)
        self.assertIn("unknown listener", str(raised.exception))

    def test_shell_action_is_rejected(self):
        config = default_config()
        config["listeners"] = [{"id": "input", "type": "explicit.ingress", "enabled": True, "config": {}}]
        config["policies"] = [{
            "id": "bad", "priority": 0, "trigger": {"types": ["test.event"]},
            "actions": [{"type": "exec.argv", "config": {"argv": ["echo", "ok"], "shell": True}}],
        }]
        with self.assertRaises(ConfigError):
            validate_config(config)

    def test_recursive_filesystem_requires_fingerprinted_acknowledgement(self):
        listener = {
            "id": "docs", "type": "filesystem.watch", "enabled": True,
            "config": {"roots": ["~/Documents"], "recursive": True},
        }
        descriptor = impact_for_listener(listener)
        self.assertTrue(descriptor["acknowledgementRequired"])
        self.assertEqual(64, len(descriptor["fingerprint"]))
        self.assertFalse(descriptor["capturesContent"])


if __name__ == "__main__":
    unittest.main()
