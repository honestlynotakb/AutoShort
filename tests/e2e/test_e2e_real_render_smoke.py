"""End-to-End (Tier B) real Chrome + FFmpeg + Node smoke test across all 3 visual styles."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cloud.audio_master import normalize_to_lufs_ffmpeg
from cloud.preflight_qa import run_chrome_smoke_check, verify_audio_mix
from cloud.style_router import scaffold_styled_project


def _has_real_toolchain() -> bool:
    if os.environ.get("RUN_REAL_E2E") != "1":
        return False
    return bool(shutil.which("node") and shutil.which("ffmpeg"))


class TestE2ERealRenderSmoke(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="e2e_real_"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    @unittest.skipUnless(_has_real_toolchain(), "Set RUN_REAL_E2E=1 with node + ffmpeg installed to run real browser smoke E2E")
    def test_real_cues_mix_and_chrome_smoke_all_styles(self):
        cases = [
            ("2d-motion", "Black Hole Gravity #shorts", "black hole event horizon"),
            ("paper-atlas", "The 1919 Molasses Flood #shorts", "1919 boston harbor molasses flood"),
            ("stick-story", "How to Survive an Avalanche #shorts", "surviving a snow avalanche burial"),
        ]
        for idx, (style, title, topic) in enumerate(cases):
            with self.subTest(style=style):
                pdir = self.tmp / f"real_{idx}"
                lines = [
                    {"text": f"What happens during {topic}?", "caps": "What *happens"},
                    {"text": "Pressure climbs rapidly while every second matters.", "caps": "Pressure *climbs"},
                    {"text": "One calm move changes the outcome.", "caps": "Calm *move", "gap": 0.2},
                ]
                scaffold_styled_project(
                    proj_dir=pdir,
                    title=title,
                    topic=topic,
                    lines=lines,
                    recent_palette_ids=[],
                    run_id=f"real-{idx}",
                    requested_style=style,
                )
                (pdir / "script.json").write_text(json.dumps({"title": title, "lines": lines}), encoding="utf-8")
                data_dir = pdir / "data"
                data_dir.mkdir(exist_ok=True)
                (data_dir / "lines.json").write_text(
                    json.dumps({"duration": 6.0, "lines": [{"s": 0.1, "e": 1.9, "text": lines[0]["text"]}, {"s": 2.1, "e": 3.9, "text": lines[1]["text"]}, {"s": 4.1, "e": 5.8, "text": lines[2]["text"]}]}),
                    encoding="utf-8",
                )
                (data_dir / "words.json").write_text(
                    json.dumps([
                        {"line": 0, "w": "What", "s": 0.1, "e": 0.5},
                        {"line": 1, "w": "Pressure", "s": 2.1, "e": 2.7},
                        {"line": 2, "w": "One", "s": 4.1, "e": 4.5},
                    ]),
                    encoding="utf-8",
                )

                cues_res = subprocess.run(["node", "tools/capture.mjs", "cues"], cwd=str(pdir), capture_output=True, text=True, timeout=60)
                self.assertEqual(cues_res.returncode, 0, f"{style} cues failed: {cues_res.stderr}")
                self.assertTrue((data_dir / "cues.json").exists())

                mix_res = subprocess.run([sys.executable, "tools/mix.py", "."], cwd=str(pdir), capture_output=True, text=True, timeout=60)
                self.assertEqual(mix_res.returncode, 0, f"{style} mix.py failed: {mix_res.stderr}")
                normalize_to_lufs_ffmpeg(data_dir / "mix.wav")
                ok_au, au_msg, _ = verify_audio_mix(data_dir / "mix.wav", expected_duration=6.0)
                self.assertTrue(ok_au, au_msg)

                ok_ch, ch_msg, _ = run_chrome_smoke_check(pdir, cover_out=pdir / "renders" / "cover.jpg")
                self.assertTrue(ok_ch, ch_msg)
                self.assertTrue((pdir / "renders" / "cover.jpg").exists())


if __name__ == "__main__":
    unittest.main()
