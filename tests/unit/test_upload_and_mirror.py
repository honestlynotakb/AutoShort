"""Unit tests for cloud.upload_youtube and cloud.upload_helper."""
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from cloud import upload_helper, upload_youtube
from cloud.state_manager import StateManager


class TestUploadAndMirrorUnit(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="unit_upload_"))
        self.vid = self.tmp / "short.mp4"
        self.vid.write_bytes(b"MP4DATA" * 100)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_upload_helper_primary_and_secondary_failover(self):
        ok_resp = MagicMock(status_code=200)
        ok_resp.json.return_value = {"success": True, "files": [{"url": "https://uguu.se/abc.mp4"}]}
        with patch("requests.post", return_value=ok_resp):
            with patch("cloud.upload_helper.verify_direct_url", return_value=True):
                self.assertEqual(upload_helper.upload_to_direct_host(self.vid), "https://uguu.se/abc.mp4")

        # Primary fails, secondary catbox.moe succeeds
        catbox_resp = MagicMock(status_code=200, text="https://files.catbox.moe/xyz.mp4\n")
        with patch("requests.post", side_effect=[RuntimeError("down")] * 3 + [catbox_resp]):
            with patch("time.sleep"):
                with patch("cloud.upload_helper.verify_direct_url", return_value=True):
                    self.assertEqual(upload_helper.upload_to_direct_host(self.vid), "https://files.catbox.moe/xyz.mp4")

    def test_verify_direct_url_head_and_range_fallback(self):
        head_bad = MagicMock(status_code=405, headers={})
        range_ok = MagicMock(status_code=206, headers={"Content-Type": "video/mp4"})
        with patch("requests.head", return_value=head_bad):
            with patch("requests.get", return_value=range_ok):
                self.assertTrue(upload_helper.verify_direct_url("https://example.com/v.mp4"))

    def test_upload_short_idempotency_and_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            upload_youtube.upload_short(self.tmp / "missing.mp4", "t", "d")

        state = StateManager(state_dir=self.tmp / "state", published_file=self.tmp / "_pub.md")
        vhash = upload_youtube.compute_file_sha256(self.vid)
        state.record_publication(
            run_id="run-idem",
            topic="T",
            title="T #shorts",
            video_hash=vhash,
            youtube_id="YT123",
            short_url="https://www.youtube.com/shorts/YT123",
            slot_id="1",
        )
        with patch("cloud.upload_youtube.get_state_manager", return_value=state):
            vid_id, url = upload_youtube.upload_short(self.vid, "T #shorts", "desc", run_id="run-idem")
        self.assertEqual(vid_id, "YT123")
        self.assertEqual(url, "https://www.youtube.com/shorts/YT123")


if __name__ == "__main__":
    unittest.main()
