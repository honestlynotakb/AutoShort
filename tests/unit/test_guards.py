"""Unit tests for TopicGuard, ScriptGuard, AssetGuard, and VideoQualityAuditor."""
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cloud.asset_guard import (
    AssetGuard,
    check_boilerplate_cards,
    compute_asset_seed,
    compute_text_sha256,
    normalize_card_text,
)
from cloud.duplicate_detector import (
    VideoQualityAuditor,
    compare_dhash_lists,
    compute_dhash_from_grayscale_9x8,
    hamming_distance,
    is_blank_or_solid_frame,
)
from cloud.script_guard import (
    ScriptGuard,
    compute_ngram_jaccard,
    compute_script_sha256,
    extract_word_ngrams,
    normalize_script_text,
)
from cloud.state_manager import StateManager
from cloud.topic_guard import (
    TopicGuard,
    compute_jaccard_similarity,
    compute_sequence_similarity,
    extract_content_tokens,
    normalize_text,
)


class TestGuardsUnit(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="unit_guards_"))
        self.state = StateManager(state_dir=self.tmp / "state", published_file=self.tmp / "_pub.md")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_topic_guard_helpers_and_thresholds(self):
        self.assertEqual(normalize_text("Why Do Stars Twinkle?!"), "why do stars twinkle")
        tokens = extract_content_tokens("Why Do Stars Twinkle in the Night Sky?")
        self.assertIn("star", tokens)
        self.assertNotIn("the", tokens)
        self.assertAlmostEqual(compute_jaccard_similarity({"a", "b"}, {"b", "c"}), 1 / 3)
        self.assertEqual(compute_jaccard_similarity(set(), set()), 0.0)
        self.assertGreater(compute_sequence_similarity("black hole", "black holes"), 0.85)

        self.state.confirm_topic_published("Why Do Stars Twinkle", "Stars #shorts", "https://youtu.be/x", "1", "r0")
        tg = TopicGuard(self.state)
        ok, _, _ = tg.evaluate_topic_uniqueness("Why Do Stars Twinkle?!")
        self.assertFalse(ok)
        ok2, _, _ = tg.evaluate_topic_uniqueness("How Submarine Periscopes Bend Light")
        self.assertTrue(ok2)

    def test_script_guard_helpers_and_overlap(self):
        norm = normalize_script_text("Hello, World! 123")
        self.assertEqual(norm, "hello world 123")
        self.assertEqual(len(compute_script_sha256("test")), 64)
        ng1 = extract_word_ngrams("one two three four five", n=3)
        ng2 = extract_word_ngrams("one two three six seven", n=3)
        self.assertGreater(compute_ngram_jaccard(ng1, ng2), 0.0)
        self.assertEqual(compute_ngram_jaccard(set(), ng1), 0.0)

        sg = ScriptGuard(self.state)
        lines = [{"text": "Deep ocean vents superheat water without boiling it."}]
        h = compute_script_sha256(sg.compile_full_text(lines))
        sg.record_approved_script(lines, "Ocean Vents", "Ocean Vents #shorts", h)
        ok, _, _ = sg.evaluate_script_uniqueness(lines, "Ocean Vents", "Ocean Vents #shorts")
        self.assertFalse(ok)

    def test_asset_guard_boilerplate_and_freshness(self):
        self.assertEqual(normalize_card_text("  320 KM/H! "), "320 km/h")
        self.assertNotEqual(compute_asset_seed("r1", "topic", 0), compute_asset_seed("r1", "topic", 1))
        ok_bp, viol = check_boilerplate_cards(["ORIGIN", "CRUCIAL PIVOT", "AFTERMATH"], topic="solar flare", title="Solar Flare", script_text="solar")
        self.assertFalse(ok_bp)
        self.assertTrue(viol)

        ag = AssetGuard(self.state)
        pdir = self.tmp / "proj"
        (pdir / "src" / "core").mkdir(parents=True)
        (pdir / "tools").mkdir(parents=True)
        files = {
            "src/core/kit2d.js": "export const P = {};",
            "src/shots.js": "export function buildShots() {}",
            "src/main.js": "window.OP = {};",
            "tools/mix.py": "# mix",
            "index.html": "<html></html>",
        }
        hashes = {}
        for rel, content in files.items():
            (pdir / rel).write_text(content, encoding="utf-8")
            hashes[rel] = compute_text_sha256(content)
        manifest = {"run_id": "r1", "file_hashes": hashes, "asset_seed": "seed1", "card_texts": ["9000 K"], "palette_id": "p1"}
        (pdir / "asset_manifest.json").write_text(__import__("json").dumps(manifest), encoding="utf-8")

        ok_f, _ = ag.verify_project_freshness(pdir, "r1")
        self.assertTrue(ok_f)
        ok_wrong_run, _ = ag.verify_project_freshness(pdir, "r2")
        self.assertFalse(ok_wrong_run)

    def test_duplicate_detector_dhash_and_video_integrity(self):
        gradient = bytes((i * 37) % 256 for i in range(72))
        h1 = compute_dhash_from_grayscale_9x8(gradient)
        self.assertEqual(len(h1), 16)
        self.assertEqual(hamming_distance(h1, h1), 0)
        self.assertTrue(is_blank_or_solid_frame(bytes([10] * 72)))
        self.assertFalse(is_blank_or_solid_frame(gradient))
        avg_dist, sim = compare_dhash_lists([h1, h1], [h1, h1])
        self.assertEqual(avg_dist, 0.0)
        self.assertEqual(sim, 1.0)

        auditor = VideoQualityAuditor(self.state)
        ok_missing, _ = auditor.validate_video_integrity(self.tmp / "nope.mp4")
        self.assertFalse(ok_missing)
        empty = self.tmp / "empty.mp4"
        empty.write_bytes(b"")
        ok_empty, _ = auditor.validate_video_integrity(empty)
        self.assertFalse(ok_empty)

        small = self.tmp / "small.mp4"
        small.write_bytes(b"0" * 600_000)
        ffprobe_json = b'{"streams": [{"codec_type": "video", "width": 1080, "height": 1920}, {"codec_type": "audio"}], "format": {"duration": "2.0"}}'
        with patch("subprocess.check_output", return_value=ffprobe_json):
            ok_short, msg = auditor.validate_video_integrity(small)
            self.assertFalse(ok_short)
            self.assertIn("short", msg.lower())


if __name__ == "__main__":
    unittest.main()
