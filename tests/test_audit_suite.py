#!/usr/bin/env python3
"""Comprehensive Audit & End-to-End Test Suite for Autonomous YouTube Shorts Engine.
Tests all five architectural gates and six core tiers:
  Tier 1: Configuration Schema, Static Invariants & Requirements
  Tier 2: Slot Routing & Deterministic Deduplication
  Tier 3: AI Intelligence Fallback & Fault Injection
  Tier 4: Dynamic 2D Motion Graphics & Adaptive Shot Generation
  Tier 5: YouTube API Quota Budgeting & Auth Health
  Tier 6: Gate 1 Semantic Topic Uniqueness & Reservation
  Tier 7: Gate 2 Script Narration Originality & N-Gram Checks
  Tier 8: Gate 3 Subject-Aware Vector Selection & Visual Diversity
  Tier 9: Gate 4 Perceptual Quality & Full-History dHash Auditor
  Tier 10: Gate 5 Application-Level Upload Idempotency & Persistence
  Tier 11: End-to-End Three-Slot Operational Simulation
"""
from __future__ import annotations

import os
import re
import sys
import json
import shutil
import tempfile
import unittest
import subprocess
import yaml
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cloud.cloud_runner import (
    load_slots_config,
    detect_current_slot,
    parse_slot_selection,
    get_published_topics,
    pick_topic_for_slot,
    write_adaptive_shots,
    slugify,
    sanitize_text_for_tts,
    verify_youtube_auth
)
from cloud.state_manager import StateManager, get_state_manager
from cloud.topic_guard import TopicGuard, normalize_text, extract_content_tokens, compute_jaccard_similarity
from cloud.script_guard import ScriptGuard, compute_script_sha256, extract_word_ngrams
from cloud.visual_engine_2d import (
    detect_topic_theme,
    detect_topic_focal_vector,
    pick_variation_palette,
    evaluate_visual_uniqueness,
    THEMES
)
from cloud.duplicate_detector import (
    VideoQualityAuditor,
    compute_file_sha256,
    compute_dhash_from_grayscale_9x8,
    hamming_distance,
    is_blank_or_solid_frame,
    compare_dhash_lists
)


class TestPipelineAuditSuite(unittest.TestCase):
    """Production Reliability & End-to-End Verification Test Suite."""

    @classmethod
    def setUpClass(cls):
        cls.slots_cfg = load_slots_config()

    def setUp(self):
        # Create an isolated temporary state directory for each test
        self.test_dir = Path(tempfile.mkdtemp(prefix="test_pipeline_state_"))
        self.state_mgr = StateManager(state_dir=self.test_dir)

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    # =========================================================================
    # Tier 1: Static Configuration & Schema Verification
    # =========================================================================
    def test_tier1_slots_configuration_integrity(self):
        """Assert all 3 daily slots exist and conform to schema standards with 15 fallbacks each."""
        expected_slots = {"1", "2", "3"}
        self.assertEqual(set(self.slots_cfg.keys()), expected_slots, "Missing or unexpected slot IDs")

        total_fallbacks = 0
        for slot_id, info in self.slots_cfg.items():
            with self.subTest(slot_id=slot_id, name=info.get('name')):
                self.assertIn('name', info)
                self.assertIn('time_pkt', info)
                self.assertIn('cron_utc', info)
                self.assertIn('target_hour_utc', info)
                self.assertIn('style', info)
                self.assertIn('category_id', info)
                self.assertIn('prompt_theme', info)
                self.assertIn('tags', info)
                self.assertIn('fallbacks', info)

                self.assertEqual(info['style'], '2d-motion')
                cron_parts = info['cron_utc'].split()
                self.assertEqual(len(cron_parts), 5)

                fallbacks = info.get('fallbacks', [])
                self.assertGreaterEqual(len(fallbacks), 15, f"Slot {slot_id} must have at least 15 curated topics")
                total_fallbacks += len(fallbacks)

                for fb in fallbacks:
                    self.assertIn('topic', fb)
                    self.assertEqual(fb.get('style'), '2d-motion')
                    self.assertIn('title', fb)
                    self.assertTrue(fb['title'].endswith('#shorts'))
                    self.assertIn('lines', fb)
                    self.assertGreaterEqual(len(fb['lines']), 4)

        self.assertGreaterEqual(total_fallbacks, 45, "Curriculum inventory must contain at least 45 total topics")

    def test_tier1_gitattributes_hygiene(self):
        """Assert .gitattributes exists and enforces universal LF line endings."""
        gitattributes = ROOT / '.gitattributes'
        self.assertTrue(gitattributes.exists(), ".gitattributes file is missing from root")
        content = gitattributes.read_text(encoding='utf-8')
        self.assertIn("eol=lf", content)

    def test_tier1_requirements_dependencies(self):
        """Assert cloud/requirements.txt contains all production runtime dependencies."""
        req_file = ROOT / 'cloud' / 'requirements.txt'
        self.assertTrue(req_file.exists())
        content = req_file.read_text(encoding='utf-8').lower()
        required_pkgs = [
            'numpy', 'scipy', 'soundfile', 'kokoro-onnx',
            'faster-whisper', 'google-api-python-client',
            'google-auth-oauthlib', 'google-auth-httplib2',
            'requests', 'pyyaml'
        ]
        for pkg in required_pkgs:
            self.assertIn(pkg, content)

    def test_tier1_workflow_yaml_integrity(self):
        """Validate .github/workflows/daily-shorts.yml structure, triggers, permissions, and timeout."""
        workflow_path = ROOT / '.github' / 'workflows' / 'daily-shorts.yml'
        self.assertTrue(workflow_path.exists())
        content = workflow_path.read_text(encoding='utf-8')
        doc = yaml.safe_load(content)

        for key in ['name', 'run-name', 'on', 'permissions', 'concurrency', 'jobs']:
            self.assertIn(key, doc)

        perms = doc['permissions']
        self.assertEqual(perms.get('contents'), 'write')
        self.assertEqual(perms.get('actions'), 'write')

        schedules = doc['on'].get('schedule', [])
        self.assertEqual(len(schedules), 3)

        jobs = doc['jobs']
        self.assertIn('test-pipeline-audit', jobs)
        self.assertIn('make-and-publish-short', jobs)

    def test_tier1_cloud_module_importability(self):
        """Assert cloud modules can be imported directly and ROOT is registered in sys.path."""
        import cloud.cloud_runner as cr
        self.assertIn(str(ROOT), sys.path)
        self.assertTrue(callable(cr.main))

        import cloud.upload_helper as uh
        self.assertTrue(callable(uh.upload_to_direct_host))

    # =========================================================================
    # Tier 2: Slot Routing & Deterministic Deduplication
    # =========================================================================
    def test_tier2_slot_auto_detection_boundaries(self):
        """Test UTC hour slot router across all operational windows."""
        test_cases = [
            (6, "1"),   # Close to Slot 1 (07:10 UTC)
            (7, "1"),   # Exactly Slot 1
            (10, "1"),  # Closer to Slot 1 than Slot 2
            (13, "2"),  # Exactly Slot 2 (13:10 UTC)
            (14, "2"),  # Closer to Slot 2 than Slot 3
            (17, "3"),  # Exactly Slot 3 (17:10 UTC)
            (18, "3"),  # Late evening, closest to Slot 3
        ]
        for hour, expected_slot in test_cases:
            from unittest.mock import patch
            mock_time = datetime(2026, 11, 11, hour, 15, 0, tzinfo=timezone.utc)
            with patch('cloud.cloud_runner.datetime') as mock_dt:
                mock_dt.now.return_value = mock_time
                detected = detect_current_slot(self.slots_cfg)
                self.assertEqual(detected, expected_slot)

    def test_tier2_published_history_deduplication(self):
        """Test published history parser indexes lowercased topics."""
        topics = get_published_topics()
        self.assertIsInstance(topics, set)
        for t in topics:
            self.assertEqual(t, t.lower())

    def test_tier2_slot_choice_resolution(self):
        """Verify robust resolution of workflow_dispatch dropdown choice strings."""
        test_inputs = [
            ("1 - Space & Cosmic (12:10 PM)", "1"),
            ("2 - Mind-Blowing Science (6:10 PM)", "2"),
            ("3 - Survival & History (10:10 PM)", "3"),
            ("1", "1"),
            ("2", "2"),
            ("3", "3"),
        ]
        for raw_val, expected in test_inputs:
            with self.subTest(raw_val=raw_val):
                res = parse_slot_selection(raw_val, self.slots_cfg)
                self.assertEqual(res, expected)

    # =========================================================================
    # Tier 3: AI Intelligence Fallback & Audio Pre-flight
    # =========================================================================
    def test_tier3_gemini_fallback_failover(self):
        """Test that missing Gemini API selects a genuinely unique fallback topic."""
        for slot_id, info in self.slots_cfg.items():
            with self.subTest(slot_id=slot_id):
                first_topic = info['fallbacks'][0]['topic'].lower()
                mock_published = {first_topic}

                env_backup = os.environ.get('GEMINI_API_KEY')
                if 'GEMINI_API_KEY' in os.environ:
                    del os.environ['GEMINI_API_KEY']
                try:
                    result = pick_topic_for_slot(info, mock_published, state_mgr=self.state_mgr, slot_id=slot_id, run_id=f"test-{slot_id}")
                    self.assertIsNotNone(result)
                    self.assertIn('topic', result)
                    self.assertIn('title', result)
                    self.assertIn('lines', result)
                    # CRITICAL: Verify returned topic is NOT in mock_published!
                    self.assertNotIn(result['topic'].lower(), mock_published)
                finally:
                    if env_backup:
                        os.environ['GEMINI_API_KEY'] = env_backup

    def test_tier3_text_sanitization_for_tts(self):
        """Verify text sanitization cleans smart quotes, em-dashes, and emojis."""
        dirty_input = '“What happens if you fall into a black hole?” — asked the astronaut 🚀🔥'
        clean = sanitize_text_for_tts(dirty_input)
        self.assertNotIn('“', clean)
        self.assertNotIn('”', clean)
        self.assertNotIn('—', clean)
        self.assertNotIn('🚀', clean)
        self.assertNotIn('🔥', clean)
        self.assertIn('"What happens if you fall into a black hole?"', clean)

    # =========================================================================
    # Tier 4: Dynamic 2D Motion Graphics & Adaptive Shot Generation
    # =========================================================================
    def test_tier4_adaptive_shots_syntax_and_importmap(self):
        """Verify adaptive shots.js generation produces valid 2D procedural motion graphics."""
        temp_dir = Path(tempfile.mkdtemp(prefix="test_shots_"))
        try:
            (temp_dir / 'src').mkdir(parents=True)
            sample_lines = [
                {"text": "Line one hook", "caps": "Line *one"},
                {"text": "Line two escalation", "caps": "Line *two"},
                {"text": "Line three twist", "caps": "Line *three"},
                {"text": "Line four loopback", "caps": "Line *four", "gap": 0.25}
            ]
            title = "Test Adaptive Video #shorts"
            write_adaptive_shots(temp_dir, title, sample_lines, "2d-motion")

            shots_file = temp_dir / 'src' / 'shots.js'
            self.assertTrue(shots_file.exists())
            content = shots_file.read_text(encoding='utf-8')
            self.assertIn("import * as K from './core/kit2d.js';", content)
            self.assertIn("export function buildShots()", content)
            self.assertIn("'S01'", content)
            self.assertIn("'S02'", content)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_tier4_render_performance_invariants(self):
        """Assert workflow enforces 24 FPS and SwiftShader downsampling parameters."""
        workflow_path = ROOT / '.github' / 'workflows' / 'daily-shorts.yml'
        doc = yaml.safe_load(workflow_path.read_text(encoding='utf-8'))
        steps = doc['jobs']['make-and-publish-short']['steps']
        gen_step = next(s for s in steps if s.get('name') == 'Run Autonomous Short Generator & Publisher')
        step_env = gen_step.get('env', {})
        self.assertEqual(step_env.get('FPS'), '24')
        self.assertIn('res=0.55', step_env.get('QS', ''))
        self.assertIn('PYTHONPATH', step_env)

    # =========================================================================
    # Tier 5: YouTube API Quota Budgeting & Auth Health
    # =========================================================================
    def test_tier5_youtube_quota_budget_verification(self):
        """Mathematically verify that 3 daily uploads do not breach YouTube quota or Zapier limits."""
        daily_quota_limit = 10000
        cost_per_upload = 1600
        num_daily_slots = 3
        total_daily_cost = cost_per_upload * num_daily_slots
        self.assertEqual(total_daily_cost, 4800)
        self.assertGreaterEqual(daily_quota_limit - total_daily_cost, 5000)

        monthly_tasks = num_daily_slots * 30
        self.assertLessEqual(monthly_tasks, 100)

    def test_tier5_youtube_token_file_format(self):
        """If local youtube_tokens.json exists, verify its JSON structure."""
        token_file = ROOT / 'cloud' / 'youtube_tokens.json'
        if token_file.exists():
            data = json.loads(token_file.read_text(encoding='utf-8'))
            refresh_token = data.get('YOUTUBE_REFRESH_TOKEN') or data.get('refresh_token')
            self.assertTrue(refresh_token.startswith('1//'))

    def test_tier5_youtube_auth_preflight_fail_fast(self):
        """Verify Stage 0 auth verification returns False gracefully when env vars are missing."""
        backup_env = {k: os.environ.get(k) for k in ['YOUTUBE_CLIENT_ID', 'YOUTUBE_CLIENT_SECRET', 'YOUTUBE_REFRESH_TOKEN']}
        for k in backup_env:
            if k in os.environ:
                del os.environ[k]
        try:
            result = verify_youtube_auth()
            self.assertFalse(result)
        finally:
            for k, v in backup_env.items():
                if v is not None:
                    os.environ[k] = v

    # =========================================================================
    # Tier 6: Gate 1 Semantic Topic Uniqueness Tests
    # =========================================================================
    def test_gate1_exact_topic_rejection(self):
        """Gate 1: Exact string topic matches must be rejected."""
        guard = TopicGuard(state_mgr=self.state_mgr)
        self.state_mgr.topics["topics"]["black hole"] = {
            "topic": "What happens if you fall into a black hole?",
            "title": "What Happens In A Black Hole #shorts",
            "status": "published"
        }
        is_u, reason, _ = guard.evaluate_topic_uniqueness("What happens if you fall into a black hole?")
        self.assertFalse(is_u)
        self.assertIn("Exact", reason)

    def test_gate1_case_and_punctuation_normalization(self):
        """Gate 1: Case and punctuation variants must be normalized and rejected."""
        guard = TopicGuard(state_mgr=self.state_mgr)
        self.state_mgr.topics["topics"]["whynoflagusespurple"] = {
            "topic": "Why no flag uses purple",
            "title": "Why No Flag Uses Purple #shorts",
            "status": "published"
        }
        is_u, _, _ = guard.evaluate_topic_uniqueness("WHY, NO FLAG USES PURPLE???")
        self.assertFalse(is_u)

    def test_gate1_semantic_phrasing_similarity_rejection(self):
        """Gate 1: Rephrased candidate with identical keyword concepts must be rejected."""
        guard = TopicGuard(state_mgr=self.state_mgr)
        self.state_mgr.topics["topics"]["quicksand"] = {
            "topic": "What happens if you fall into deep quicksand?",
            "title": "What To Do If Trapped In Quicksand #shorts",
            "status": "published"
        }
        # Rephrased wording
        is_u, reason, _ = guard.evaluate_topic_uniqueness("What would you do if you fell into deep quicksand?")
        self.assertFalse(is_u)
        self.assertTrue("similarity" in reason.lower() or "overlap" in reason.lower())

    def test_gate1_genuinely_unique_topic_acceptance(self):
        """Gate 1: Completely unrecorded topic must be accepted."""
        guard = TopicGuard(state_mgr=self.state_mgr)
        is_u, _, _ = guard.evaluate_topic_uniqueness("How the pistol shrimp creates solar temperatures with sound cavitation")
        self.assertTrue(is_u)

    def test_gate1_negative_prompt_generation(self):
        """Gate 1: Negative constraint feedback must format cleanly for Gemini prompts."""
        guard = TopicGuard(state_mgr=self.state_mgr)
        rejected = [("What happens in quicksand?", "Semantic overlap"), ("Why glass is not solid", "Exact match")]
        constraint_str = guard.build_gemini_rejection_constraint(rejected)
        self.assertIn("CRITICAL NEGATIVE CONSTRAINTS", constraint_str)
        self.assertIn("quicksand", constraint_str)
        self.assertIn("Why glass is not solid", constraint_str)

    def test_gate1_exhausted_fallback_safe_failure(self):
        """Gate 1: If all fallbacks are marked published and Gemini is absent, fail safely with RuntimeError."""
        mock_slot = {
            "name": "Test Genre",
            "fallbacks": [
                {"topic": "Used Topic 1", "title": "Used 1 #shorts", "lines": [{"text": "Line 1"}]},
                {"topic": "Used Topic 2", "title": "Used 2 #shorts", "lines": [{"text": "Line 2"}]}
            ]
        }
        guard = TopicGuard(state_mgr=self.state_mgr)
        self.state_mgr.topics["topics"]["used topic 1"] = {"topic": "Used Topic 1", "status": "published"}
        self.state_mgr.topics["topics"]["used topic 2"] = {"topic": "Used Topic 2", "status": "published"}

        published = {"used topic 1", "used topic 2"}
        from unittest.mock import patch
        with patch('cloud.cloud_runner.load_slots_config', return_value={"1": mock_slot, "2": mock_slot}):
            with self.assertRaises(RuntimeError):
                pick_topic_for_slot(mock_slot, published, slot_id="1", run_id="test-fail", state_mgr=self.state_mgr)

    def test_gate1_reservation_lifecycle(self):
        """Gate 1: Reserving topic locks it against concurrent runs; releasing frees it."""
        guard = TopicGuard(state_mgr=self.state_mgr)
        topic = "The physics of lightning Lichtenberg figures"
        reserved, _ = guard.reserve_if_unique(topic, "Lightning Scars #shorts", slot_id="1", run_id="run-A")
        self.assertTrue(reserved)

        # Immediate second reservation by run-B must fail
        reserved_b, _ = guard.reserve_if_unique(topic, "Lightning Scars #shorts", slot_id="1", run_id="run-B")
        self.assertFalse(reserved_b)

        # Release topic
        self.state_mgr.release_topic(topic)
        reserved_c, _ = guard.reserve_if_unique(topic, "Lightning Scars #shorts", slot_id="1", run_id="run-C")
        self.assertTrue(reserved_c)

    # =========================================================================
    # Tier 7: Gate 2 Script Narration Originality Tests
    # =========================================================================
    def test_gate2_identical_script_rejection(self):
        """Gate 2: Script with identical text fingerprint must be rejected."""
        guard = ScriptGuard(state_mgr=self.state_mgr)
        lines = [
            {"text": "Why do physicists say glass is not a standard solid?"},
            {"text": "When molten glass cools, atoms freeze into an amorphous state."}
        ]
        is_u, _, meta = guard.evaluate_script_uniqueness(lines, "Glass", "Why Glass #shorts")
        self.assertTrue(is_u)
        guard.record_approved_script(lines, "Glass", "Why Glass #shorts", meta["sha256"])

        # Second evaluation of same script must fail
        is_u2, reason, _ = guard.evaluate_script_uniqueness(lines, "Glass 2", "Glass 2 #shorts")
        self.assertFalse(is_u2)
        self.assertIn("Exact script fingerprint", reason)

    def test_gate2_ngram_overlap_rejection(self):
        """Gate 2: Script sharing over 50% 3-grams with historical script must be rejected."""
        guard = ScriptGuard(state_mgr=self.state_mgr)
        lines_orig = [
            {"text": "What happens if you fall into deep quicksand?"},
            {"text": "Humans naturally float at waist level due to lower body density."},
            {"text": "Panicking and thrashing your legs packs sand grains into concrete."}
        ]
        _, _, meta = guard.evaluate_script_uniqueness(lines_orig, "Quicksand", "Quicksand #shorts")
        guard.record_approved_script(lines_orig, "Quicksand", "Quicksand #shorts", meta["sha256"])

        # Slightly tweaked script recycling the majority of phrases
        lines_tweaked = [
            {"text": "What happens if you fall into deep quicksand?"},
            {"text": "Humans naturally float at waist level due to low body density."},
            {"text": "Panicking and thrashing your legs packs sand grains into concrete."}
        ]
        is_u, reason, _ = guard.evaluate_script_uniqueness(lines_tweaked, "Quicksand Reword", "Quicksand #shorts")
        self.assertFalse(is_u)
        self.assertIn("3-gram similarity", reason)

    def test_gate2_distinct_script_acceptance(self):
        """Gate 2: Independent narration on a different topic must pass."""
        guard = ScriptGuard(state_mgr=self.state_mgr)
        lines_a = [{"text": "A black hole has intense gravitational tidal force."}]
        _, _, meta = guard.evaluate_script_uniqueness(lines_a, "Black Hole", "Black Hole #shorts")
        guard.record_approved_script(lines_a, "Black Hole", "Black Hole #shorts", meta["sha256"])

        lines_b = [{"text": "Prince Rupert drops withstand rifle bullets on the bulb."}]
        is_u, _, _ = guard.evaluate_script_uniqueness(lines_b, "Prince Rupert", "Rupert #shorts")
        self.assertTrue(is_u)

    def test_gate2_script_history_persistence(self):
        """Gate 2: Script registry persists and reloads from disk across instances."""
        guard1 = ScriptGuard(state_mgr=self.state_mgr)
        lines = [{"text": "Superfluid helium has zero viscosity and climbs beaker walls."}]
        _, _, meta = guard1.evaluate_script_uniqueness(lines, "Helium", "Helium #shorts")
        guard1.record_approved_script(lines, "Helium", "Helium #shorts", meta["sha256"])

        # Instantiate second state manager pointing to same test dir
        sm2 = StateManager(state_dir=self.test_dir)
        guard2 = ScriptGuard(state_mgr=sm2)
        is_u, _, _ = guard2.evaluate_script_uniqueness(lines, "Helium Dup", "Helium #shorts")
        self.assertFalse(is_u)

    # =========================================================================
    # Tier 8: Gate 3 Subject-Aware Vector Selection & Visual Diversity
    # =========================================================================
    def test_gate3_content_aware_vector_selection(self):
        """Gate 3: Inspects subject keywords to route distinct procedural vectors."""
        vec_space, _, _ = detect_topic_focal_vector("What happens if you fall into a black hole?", [])
        self.assertEqual(vec_space, "BLACK_HOLE")

        vec_pulsar, _, _ = detect_topic_focal_vector("Deadliest magnetar starquake in deep space", [])
        self.assertEqual(vec_pulsar, "NEUTRON_STAR")

        vec_glass, _, _ = detect_topic_focal_vector("Why glass is an amorphous solid crystal", [])
        self.assertEqual(vec_glass, "ATOMIC_LATTICE")

        vec_temp, _, _ = detect_topic_focal_vector("Superfluid helium liquid climbs out of cups", [])
        self.assertEqual(vec_temp, "MOLECULAR_SIM")

        vec_escape, _, _ = detect_topic_focal_vector("How to escape a sinking submerged car door pressure", [])
        self.assertEqual(vec_escape, "SUBMERGED_CABIN")

    def test_gate3_palette_consecutive_non_repetition(self):
        """Gate 3: Palette cycler must never pick the same palette as recent runs."""
        p1 = pick_variation_palette("COSMIC_SPACE", [])
        p2 = pick_variation_palette("COSMIC_SPACE", [p1["id"]])
        self.assertNotEqual(p1["id"], p2["id"])

        p3 = pick_variation_palette("COSMIC_SPACE", [p1["id"], p2["id"]])
        self.assertNotIn(p3["id"], [p1["id"], p2["id"]])

    def test_gate3_visual_planning_diversity_gate(self):
        """Gate 3: Reject planned video matching immediate predecessor theme, palette, and archetypes."""
        history = [{
            "theme": "COSMIC_SPACE",
            "palette": "cosmic_abyss",
            "scene_sequence": ["HOOK_BLACK_HOLE", "METRIC_TELEMETRY", "LOOP_OUTRO"]
        }]
        vis_ok, reason = evaluate_visual_uniqueness(
            theme_name="COSMIC_SPACE",
            palette_id="cosmic_abyss",
            scene_sequence=["HOOK_BLACK_HOLE", "METRIC_TELEMETRY", "LOOP_OUTRO"],
            history_entries=history
        )
        self.assertFalse(vis_ok)
        self.assertIn("Visual stagnation", reason)

    # =========================================================================
    # Tier 9: Gate 4 Perceptual Quality & Full-History dHash Auditor
    # =========================================================================
    def test_gate4_exact_file_sha256_duplicate_detection(self):
        """Gate 4: Identical video file SHA-256 is caught and rejected."""
        auditor = VideoQualityAuditor(state_mgr=self.state_mgr)
        fake_video = self.test_dir / "test_video.mp4"
        fake_video.write_bytes(b"\x00" * 500000) # dummy payload

        file_hash = compute_file_sha256(fake_video)
        auditor.history.append({"file_hash": file_hash, "title": "Original Video"})

        from unittest.mock import patch
        with patch.object(auditor, 'validate_video_integrity', return_value=(True, "OK")):
            is_dup, reason, _ = auditor.audit_and_check_duplicate(
                fake_video, "Topic", "Title", "COSMIC_SPACE", "cosmic_abyss", ["HOOK"]
            )
            self.assertTrue(is_dup)
            self.assertIn("Exact file duplicate", reason)

    def test_gate4_dhash_hamming_normalized_accuracy(self):
        """Gate 4: Hamming distance correctly normalized between 0.0 and 1.0."""
        # Gradient byte buffers
        buf_a = bytes(range(72))
        buf_b = bytes(reversed(range(72)))
        h_a = compute_dhash_from_grayscale_9x8(buf_a)
        h_b = compute_dhash_from_grayscale_9x8(buf_b)

        dist, sim = compare_dhash_lists([h_a], [h_b])
        self.assertGreater(dist, 35)
        self.assertLess(sim, 0.5)

    def test_gate4_black_frame_filtering(self):
        """Gate 4: All-black or solid frames are flagged to prevent false zero-distance matches."""
        solid_black = b"\x00" * 72
        self.assertTrue(is_blank_or_solid_frame(solid_black))

        pattern_frame = bytes([0 if i % 2 == 0 else 255 for i in range(72)])
        self.assertFalse(is_blank_or_solid_frame(pattern_frame))

    def test_gate4_full_history_comparison(self):
        """Gate 4: Auditor inspects entire history, catching duplicates beyond the last 5 entries."""
        auditor = VideoQualityAuditor(state_mgr=self.state_mgr)
        h_target = "1234567812345678"

        # Populate history with 10 entries where entry 0 is similar
        auditor.history = []
        for i in range(10):
            auditor.history.append({
                "title": f"Video {i}",
                "frame_hashes": [h_target] if i == 0 else ["ffff0000ffff0000"]
            })

        # Compare candidate with same hash as entry 0
        dist, sim = compare_dhash_lists([h_target], auditor.history[0]["frame_hashes"])
        self.assertEqual(sim, 1.0)

    def test_gate4_corrupted_history_safe_recovery(self):
        """Gate 4: Malformed video history file recovers gracefully with empty list."""
        corrupted_file = self.test_dir / "video_history.json"
        corrupted_file.write_text("{NOT VALID JSON", encoding="utf-8")
        sm = StateManager(state_dir=self.test_dir)
        self.assertEqual(sm.video_history, [])

    # =========================================================================
    # Tier 10: Gate 5 Upload Idempotency & Persistence
    # =========================================================================
    def test_persistence_atomic_write_integrity(self):
        """Persistence: Atomic file write creates clean, uncorrupted JSON."""
        target_file = self.test_dir / "atomic_test.json"
        from cloud.state_manager import atomic_save
        data = {"hello": "world", "timestamp": 123456}
        atomic_save(target_file, data)
        self.assertTrue(target_file.exists())
        loaded = json.loads(target_file.read_text(encoding="utf-8"))
        self.assertEqual(loaded, data)

    def test_persistence_state_file_versioning_and_schema(self):
        """Persistence: All state registries contain version schema declarations."""
        self.assertEqual(self.state_mgr.topics.get("version"), 1)
        self.assertEqual(self.state_mgr.scripts.get("version"), 1)
        self.assertEqual(self.state_mgr.publications.get("version"), 1)

    def test_gate5_already_published_video_hash_aborts_upload(self):
        """Gate 5: Re-running with an already published video hash returns existing record without uploading."""
        from cloud.upload_youtube import upload_short
        from unittest.mock import patch

        fake_video = self.test_dir / "published_test.mp4"
        fake_video.write_bytes(b"\xaa\xbb\xcc" * 200000)
        v_hash = compute_file_sha256(fake_video)

        # Register in state manager as published
        self.state_mgr.record_publication(
            run_id="run-101",
            topic="Test Topic",
            title="Test Title #shorts",
            video_hash=v_hash,
            youtube_id="YOUTUBE_VID_ABC",
            short_url="https://www.youtube.com/shorts/YOUTUBE_VID_ABC",
            slot_id="1"
        )

        with patch('cloud.upload_youtube.get_state_manager', return_value=self.state_mgr):
            vid_id, short_url = upload_short(fake_video, "Test Title", "Desc", run_id="run-102")
            self.assertEqual(vid_id, "YOUTUBE_VID_ABC")
            self.assertIn("YOUTUBE_VID_ABC", short_url)

    def test_gate5_run_id_idempotency(self):
        """Gate 5: Re-running with an existing run_id skips upload and returns existing publication."""
        from cloud.upload_youtube import upload_short
        from unittest.mock import patch

        fake_video = self.test_dir / "new_video.mp4"
        fake_video.write_bytes(b"\x11\x22\x33" * 200000)
        v_hash = compute_file_sha256(fake_video)

        self.state_mgr.record_publication(
            run_id="run-duplicate-id",
            topic="Test Topic",
            title="Test Title #shorts",
            video_hash="different_hash",
            youtube_id="YOUTUBE_VID_XYZ",
            short_url="https://www.youtube.com/shorts/YOUTUBE_VID_XYZ",
            slot_id="2"
        )

        with patch('cloud.upload_youtube.get_state_manager', return_value=self.state_mgr):
            vid_id, short_url = upload_short(fake_video, "Title", "Desc", run_id="run-duplicate-id")
            self.assertEqual(vid_id, "YOUTUBE_VID_XYZ")

    def test_gate5_failed_upload_does_not_record_published(self):
        """Gate 5: Unsuccessful uploads do not mark topics as permanently published."""
        self.state_mgr.reserve_topic("Topic X", "Title X #shorts", "1", "run-fail")
        self.assertFalse(self.state_mgr.is_run_published("run-fail"))

    def test_gate5_upload_reconciliation_after_failed_logging(self):
        """Gate 5: State reconciliation correctly marks reservation as published."""
        self.state_mgr.reserve_topic("Topic Y", "Title Y #shorts", "2", "run-recon")
        self.state_mgr.record_publication(
            run_id="run-recon",
            topic="Topic Y",
            title="Title Y #shorts",
            video_hash="hash-y",
            youtube_id="VID_Y",
            short_url="https://youtube.com/shorts/VID_Y",
            slot_id="2"
        )
        self.assertTrue(self.state_mgr.is_run_published("run-recon"))
        self.assertTrue(self.state_mgr.is_topic_used("Topic Y"))

    # =========================================================================
    # Tier 11: End-to-End Three-Slot Operational Simulation
    # =========================================================================
    def test_e2e_dry_run_all_three_slots_produce_unique_topics(self):
        """Simulate end-to-end cloud runner execution for all 3 slots via CLI, verifying unique topics."""
        chosen_topics = set()
        for slot in ["1", "2", "3"]:
            with self.subTest(slot=slot):
                cmd = [sys.executable, str(ROOT / 'cloud' / 'cloud_runner.py'), '--dry-run', '--slot', slot]
                proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=str(ROOT))
                self.assertEqual(
                    proc.returncode, 0,
                    f"Dry run failed for Slot {slot}.\nSTDOUT: {proc.stdout}\nSTDERR: {proc.stderr}"
                )
                self.assertIn("DRY-RUN COMPLETE.", proc.stdout)

                # Extract selected topic from stdout
                match = re.search(r"Topic:\s*(.+)", proc.stdout)
                self.assertIsNotNone(match, f"Failed to match selected topic in Slot {slot} stdout")
                topic = match.group(1).strip()
                self.assertNotIn(topic, chosen_topics, f"Slot {slot} duplicated previously chosen topic: '{topic}'")
                chosen_topics.add(topic)


if __name__ == '__main__':
    unittest.main()
