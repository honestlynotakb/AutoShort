"""End-to-End (Tier A) mocked pipeline tests for cloud.cloud_runner.main()."""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cloud import cloud_runner
from cloud.state_manager import StateManager


class TestE2EPipelineMocked(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="e2e_mocked_"))
        self.state_dir = self.tmp / "state"
        self.pub_file = self.tmp / "_published.md"
        self.projects_dir = self.tmp / "projects"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _fake_run_cmd(self, cmd, cwd=None, env=None):
        cdir = Path(cwd) if cwd else self.projects_dir
        if "capture.mjs video" in cmd:
            # Extract quoted output path e.g. renders/slug.mp4
            rel = cmd.split('"')[1]
            out_mp4 = cdir / rel
            out_mp4.parent.mkdir(parents=True, exist_ok=True)
            out_mp4.write_bytes(b"FAKE_MP4_BYTES" * 200)
        elif "capture.mjs cues" in cmd:
            (cdir / "data").mkdir(parents=True, exist_ok=True)
            (cdir / "data" / "cues.json").write_text('{"duration": 10.0, "cues": []}', encoding="utf-8")
        elif "mix.py" in cmd:
            (cdir / "data").mkdir(parents=True, exist_ok=True)
            (cdir / "data" / "mix.wav").write_bytes(b"RIFF" + b"\x00" * 64)

    def test_e2e_happy_path_stage_0_to_5(self):
        argv = [
            "cloud_runner.py",
            "--slot", "1",
            "--state-dir", str(self.state_dir),
            "--published-file", str(self.pub_file),
        ]
        with patch.object(sys, "argv", argv):
            with patch.object(cloud_runner, "PROJECTS_DIR", self.projects_dir):
                with patch.dict("os.environ", {"GEMINI_API_KEY": "", "YOUTUBE_CLIENT_ID": ""}):
                    with patch("cloud.cloud_runner.run_cmd", side_effect=self._fake_run_cmd):
                        with patch("cloud.cloud_runner.normalize_to_lufs_ffmpeg", return_value={"applied": True, "after_metrics": {"lufs": -14.0, "peak_dbfs": -1.0}}):
                            with patch("cloud.cloud_runner.verify_whisper_alignment", return_value=(True, "ok", {"duration_sec": 10.0})):
                                with patch("cloud.cloud_runner.verify_audio_mix", return_value=(True, "ok", {})):
                                    with patch("cloud.cloud_runner.run_chrome_smoke_check") as mock_smoke:
                                        def _smoke(pdir, cover_out=None, min_hook_luma=18.0):
                                            if cover_out:
                                                Path(cover_out).parent.mkdir(parents=True, exist_ok=True)
                                                Path(cover_out).write_bytes(b"JPG")
                                            return True, "ok", {"hook_luma": 120.0}
                                        mock_smoke.side_effect = _smoke
                                        with patch("cloud.duplicate_detector.VideoQualityAuditor.audit_and_check_duplicate", return_value=(False, "unique", {"duration_sec": 10.0, "video_hash": "h1", "dhashes": []})):
                                            cloud_runner.main()

        proj_dirs = list(self.projects_dir.iterdir())
        self.assertEqual(len(proj_dirs), 1)
        pdir = proj_dirs[0]
        self.assertTrue((pdir / "script.json").exists())
        self.assertTrue((pdir / "asset_manifest.json").exists())
        self.assertTrue((pdir / "renders" / "cover.jpg").exists())
        self.assertTrue((pdir / "renders" / "release_metadata.json").exists())
        self.assertTrue(list((pdir / "renders").glob("*.mp4")))
        self.assertTrue(self.pub_file.exists())

    def test_e2e_gate3c_failure_releases_topic_reservation(self):
        argv = [
            "cloud_runner.py",
            "--slot", "1",
            "--state-dir", str(self.state_dir),
            "--published-file", str(self.pub_file),
        ]
        with patch.object(sys, "argv", argv):
            with patch.object(cloud_runner, "PROJECTS_DIR", self.projects_dir):
                with patch.dict("os.environ", {"GEMINI_API_KEY": "", "REQUIRE_WHISPER": "1"}):
                    with patch("cloud.cloud_runner.run_cmd", side_effect=self._fake_run_cmd):
                        with patch("cloud.cloud_runner.normalize_to_lufs_ffmpeg", return_value={"applied": False, "after_metrics": {}}):
                            with patch("cloud.cloud_runner.verify_whisper_alignment", return_value=(False, "uniform fallback", {})):
                                with self.assertRaises(RuntimeError):
                                    cloud_runner.main()

        mgr = StateManager(state_dir=self.state_dir, published_file=self.pub_file)
        reserved = [k for k, v in mgr.topics["topics"].items() if v.get("status") == "reserved"]
        self.assertEqual(reserved, [])

    def test_e2e_gate4_duplicate_releases_topic_reservation(self):
        argv = [
            "cloud_runner.py",
            "--slot", "1",
            "--state-dir", str(self.state_dir),
            "--published-file", str(self.pub_file),
        ]
        with patch.object(sys, "argv", argv):
            with patch.object(cloud_runner, "PROJECTS_DIR", self.projects_dir):
                with patch.dict("os.environ", {"GEMINI_API_KEY": ""}):
                    with patch("cloud.cloud_runner.run_cmd", side_effect=self._fake_run_cmd):
                        with patch("cloud.cloud_runner.normalize_to_lufs_ffmpeg", return_value={"applied": True, "after_metrics": {"lufs": -14.0, "peak_dbfs": -1.0}}):
                            with patch("cloud.cloud_runner.verify_whisper_alignment", return_value=(True, "ok", {"duration_sec": 10.0})):
                                with patch("cloud.cloud_runner.verify_audio_mix", return_value=(True, "ok", {})):
                                    with patch("cloud.cloud_runner.run_chrome_smoke_check", return_value=(True, "ok", {})):
                                        with patch("cloud.duplicate_detector.VideoQualityAuditor.audit_and_check_duplicate", return_value=(True, "duplicate video", {})):
                                            with self.assertRaises(ValueError):
                                                cloud_runner.main()

        mgr = StateManager(state_dir=self.state_dir, published_file=self.pub_file)
        reserved = [k for k, v in mgr.topics["topics"].items() if v.get("status") == "reserved"]
        self.assertEqual(reserved, [])


if __name__ == "__main__":
    unittest.main()
