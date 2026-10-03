from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PluginContractTests(unittest.TestCase):
    def test_manifest_matches_omarchy_schema_one_safety_contract(self):
        manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(1, manifest["schemaVersion"])
        self.assertEqual("uriak.omr-notifications", manifest["id"])
        self.assertFalse(manifest["id"].startswith("omarchy."))
        self.assertEqual({"service", "bar-widget"}, set(manifest["kinds"]))
        for entry in manifest["entryPoints"].values():
            self.assertFalse(entry.startswith("/"))
            self.assertNotIn("..", entry)
            self.assertTrue((ROOT / entry).is_file())

    def test_all_versioned_schema_documents_are_json_objects(self):
        schemas = sorted((ROOT / "schemas").glob("*.json"))
        self.assertGreaterEqual(len(schemas), 7)
        for path in schemas:
            value = json.loads(path.read_text(encoding="utf-8"))
            self.assertIsInstance(value, dict, path.name)
            self.assertIn("$schema", value, path.name)


if __name__ == "__main__":
    unittest.main()
