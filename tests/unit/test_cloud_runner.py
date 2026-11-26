"""Unit tests for cloud.cloud_runner."""
import io
import json
import shutil
import subprocess
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

from cloud import cloud_runner
from cloud.state_manager import StateManager


class _DummyHTTPResponse:
    def __init__(self, payload: dict):
        self._raw = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._raw

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class TestCloudRunnerUnit(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="unit_runner_"))
        self.state = StateManager(state_dir=self.tmp / "state", published_file=self.tmp / "_pub.md")
        self.slots_cfg = cloud_runner.load_slots_config()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_slugify_and_sanitize_text_for_tts(self):
        self.assertEqual(cloud_runner.slugify("Hello, World! #shorts"), "hello-world-shorts")
        cleaned = cloud_runner.sanitize_text_for_tts("“Smart” — dash 🚀 100%")
        self.assertNotIn("🚀", cleaned)
        self.assertIn('"Smart"', cleaned)
        self.assertIn("-", cleaned)

    def test_generate_with_gemini_valid_and_retries_429(self):
        valid_payload = {
            "topic": "Magnetar Starquakes",
            "title": "Starquakes Bend Space #shorts",
            "lines": [{"text": "A magnetar crust cracks in milliseconds."}],
        }
        good_resp = _DummyHTTPResponse({"candidates": [{"content": {"parts": [{"text": json.dumps(valid_payload)}]}}]})
        err_429 = urllib.error.HTTPError("https://api.example.com", 429, "Too Many Requests", {}, io.BytesIO(b"rate limit"))

        with patch("urllib.request.urlopen", side_effect=[err_429, good_resp]):
            with patch("time.sleep"):
                res = cloud_runner.generate_with_gemini("fake-key", set(), self.slots_cfg["1"], state_mgr=self.state)
        self.assertEqual(res["topic"], "Magnetar Starquakes")

    def test_generate_with_gemini_raises_when_all_endpoints_fail(self):
        bad_resp = _DummyHTTPResponse({"candidates": [{"content": {"parts": [{"text": "not json at all"}]}}]})
        with patch.dict("os.environ", {"GEMINI_MODELS": "gemini-test"}):
            with patch("urllib.request.urlopen", return_value=bad_resp):
                with self.assertRaises(ValueError):
                    cloud_runner.generate_with_gemini("fake-key", set(), self.slots_cfg["1"], state_mgr=self.state)

    def test_pick_topic_for_slot_uses_gemini_then_fails_over_to_curriculum(self):
        with patch.dict("os.environ", {"GEMINI_API_KEY": "fake-key"}):
            with patch("cloud.cloud_runner.generate_with_gemini", side_effect=ValueError("down")):
                with patch("time.sleep"):
                    item = cloud_runner.pick_topic_for_slot(
                        self.slots_cfg["1"], set(), slot_id="1", run_id="r-test", state_mgr=self.state
                    )
        self.assertIn("topic", item)
        self.assertIn("_script_meta", item)

    def test_run_cmd_raises_on_nonzero_exit(self):
        fake_proc = MagicMock()
        fake_proc.stdout = io.StringIO("step failed\n")
        fake_proc.wait.return_value = 2
        with patch("subprocess.Popen", return_value=fake_proc):
            with self.assertRaises(RuntimeError):
                cloud_runner.run_cmd("fake cmd", cwd=self.tmp)


if __name__ == "__main__":
    unittest.main()
