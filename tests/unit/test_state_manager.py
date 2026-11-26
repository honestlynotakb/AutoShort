"""Unit tests for cloud.state_manager."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cloud.state_manager import StateManager, atomic_save, load_json_safe


class TestStateManagerUnit(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="unit_state_"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_atomic_save_and_load_json_safe(self):
        target = self.tmp / "nested" / "data.json"
        payload = {"key": "value", "items": [1, 2, 3]}
        atomic_save(target, payload)
        self.assertTrue(target.exists())
        self.assertEqual(load_json_safe(target, {}), payload)

    def test_load_json_safe_recovers_missing_and_corrupted(self):
        self.assertEqual(load_json_safe(self.tmp / "missing.json", {"d": 1}), {"d": 1})
        bad = self.tmp / "bad.json"
        bad.write_text("{not valid json", encoding="utf-8")
        self.assertEqual(load_json_safe(bad, ["fallback"]), ["fallback"])

    def test_atomic_save_retries_permission_error_then_falls_back(self):
        target = self.tmp / "locked.json"
        with patch("pathlib.Path.replace", side_effect=PermissionError("WinError 5")):
            with patch("time.sleep"):
                atomic_save(target, {"ok": True})
        self.assertEqual(json.loads(target.read_text(encoding="utf-8")), {"ok": True})
        leftovers = list(self.tmp.glob("*.tmp.*"))
        self.assertEqual(leftovers, [])

    def test_topic_reservation_release_and_published_bootstrap(self):
        pub_md = self.tmp / "_published.md"
        pub_md.write_text(
            "| Date | Topic | Style | Title | URL |\n"
            "|---|---|---|---|---|\n"
            "| 2026-01-01 | Why the Sky Is Blue | 2d-motion | Sky Color #shorts | https://youtu.be/abc |\n",
            encoding="utf-8",
        )
        mgr = StateManager(state_dir=self.tmp / "state", published_file=pub_md)
        self.assertIn("why the sky is blue", mgr.topics["topics"])
        self.assertEqual(mgr.topics["topics"]["why the sky is blue"]["status"], "published")

        mgr.reserve_topic("New Topic X", "New Topic X #shorts", "slot1", "run-1")
        self.assertEqual(mgr.topics["topics"]["new topic x"]["status"], "reserved")

        mgr.release_topic("New Topic X")
        self.assertNotIn("new topic x", mgr.topics["topics"])


if __name__ == "__main__":
    unittest.main()
