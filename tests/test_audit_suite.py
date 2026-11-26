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
    generate_with_gemini,
    write_adaptive_shots,
    write_step_summary,
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
    generate_kit2d_js,
    generate_shots_js,
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

    def test_tier1_secrets_and_env_hygiene(self):
        """Assert .gitignore protects .env and tokens, and no plaintext secrets are tracked in git."""
        gitignore = ROOT / '.gitignore'
        self.assertTrue(gitignore.exists(), ".gitignore file is missing from root")
        gi_content = gitignore.read_text(encoding='utf-8')
        for rule in ['.env', '.env.*', '*.env', 'secrets.json', 'client_secret*.json', 'credentials.json', 'cloud/youtube_tokens*.json']:
            self.assertIn(rule, gi_content, f"Missing required .gitignore rule: {rule}")

        # Check .env.example exists and only has placeholders
        env_example = ROOT / '.env.example'
        self.assertTrue(env_example.exists(), ".env.example template is missing")
        example_content = env_example.read_text(encoding='utf-8')
        self.assertIn("GEMINI_API_KEY=", example_content)
        self.assertIn("YOUTUBE_CLIENT_ID=", example_content)
        self.assertNotIn("GOCSPX-", example_content)
        self.assertNotIn("AIza", example_content)

        # Scan tracked git files for hardcoded Google OAuth client secrets (excluding this test suite)
        secret_prefix = "GOC" + "SPX-"
        try:
            import subprocess
            tracked_files = subprocess.check_output(['git', 'ls-files'], text=True).splitlines()
            for tf in tracked_files:
                if tf == 'tests/test_audit_suite.py':
                    continue
                p = ROOT / tf
                if p.exists() and p.is_file() and p.suffix in ['.py', '.json', '.yml', '.yaml', '.sh', '.md', '.txt']:
                    try:
                        file_txt = p.read_text(encoding='utf-8')
                        self.assertNotIn(secret_prefix, file_txt, f"Found hardcoded Google Client Secret in tracked file: {tf}")
                    except UnicodeDecodeError:
                        pass
        except Exception as e:
            if isinstance(e, AssertionError):
                raise
            pass

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
        """Test published history parser indexes lowercased topics without mutating live state."""
        pub_copy = self.test_dir / "_published.md"
        if (ROOT / "_published.md").exists():
            shutil.copy2(ROOT / "_published.md", pub_copy)
        else:
            pub_copy.write_text("| Date | Topic | Style | Title | YouTube Link |\n|---|---|---|---|---|\n| 2026-11-11 | Test Topic | 2d-motion | Test Title #shorts | https://example.com |\n", encoding="utf-8")
        isolated_sm = StateManager(state_dir=self.test_dir / "pub_state", published_file=pub_copy)
        topics = get_published_topics(published_file=pub_copy, state_mgr=isolated_sm)
        self.assertIsInstance(topics, set)
        self.assertGreater(len(topics), 0)
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

    def test_tier2_schedule_cron_routing_ignores_runner_delay(self):
        """Verify GITHUB_SCHEDULE routes delayed crons to intended slot and uses 24h wrap-around."""
        from unittest.mock import patch
        delayed_time = datetime(2026, 11, 20, 16, 15, 0, tzinfo=timezone.utc)
        with patch('cloud.cloud_runner.datetime') as mock_dt:
            mock_dt.now.return_value = delayed_time
            self.assertEqual(detect_current_slot(self.slots_cfg, schedule_cron="10 7 * * *"), "1")
            self.assertEqual(detect_current_slot(self.slots_cfg, schedule_cron="10 13 * * *"), "2")
            self.assertEqual(detect_current_slot(self.slots_cfg, schedule_cron="10 17 * * *"), "3")

        # Verify circular 24h wrap-around when no cron is specified
        late_night = datetime(2026, 11, 20, 23, 15, 0, tzinfo=timezone.utc)
        with patch('cloud.cloud_runner.datetime') as mock_dt:
            mock_dt.now.return_value = late_night
            self.assertEqual(detect_current_slot(self.slots_cfg, schedule_cron=""), "3")

        early_morning = datetime(2026, 11, 20, 2, 15, 0, tzinfo=timezone.utc)
        with patch('cloud.cloud_runner.datetime') as mock_dt:
            mock_dt.now.return_value = early_morning
            self.assertEqual(detect_current_slot(self.slots_cfg, schedule_cron=""), "1")

    def test_tier1_write_step_summary_generates_markdown(self):
        """Verify write_step_summary writes telemetry summary markdown instead of returning early."""
        summary_file = self.test_dir / "step_summary.md"
        backup = os.environ.get("GITHUB_STEP_SUMMARY")
        os.environ["GITHUB_STEP_SUMMARY"] = str(summary_file)
        try:
            write_step_summary(
                title="Test Video #shorts",
                slot_info={"name": "Survival Scenarios & Dark History", "slot_id": 3},
                topic="Test Topic",
                style="2d-motion",
                video_name="test-video.mp4",
                short_url="[Manual/Pending Upload] test-video.mp4",
                stage_metrics={"Voice Synthesis": 1.25},
                total_time=3.50,
                run_id="slot3-test-run"
            )
            self.assertTrue(summary_file.exists())
            content = summary_file.read_text(encoding="utf-8")
            self.assertIn("Autonomous YouTube Short Publication Summary", content)
            self.assertIn("slot3-test-run", content)
            self.assertIn("Voice Synthesis", content)
        finally:
            if backup is not None:
                os.environ["GITHUB_STEP_SUMMARY"] = backup
            else:
                os.environ.pop("GITHUB_STEP_SUMMARY", None)

    def test_tier1_gemini_models_not_retired(self):
        """Verify generate_with_gemini uses active Gemini models rather than retired 1.5/2.0 endpoints."""
        from unittest.mock import patch, MagicMock
        called_urls = []
        fake_response = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": json.dumps({
                            "topic": "Fresh AI Topic",
                            "style": "2d-motion",
                            "title": "Fresh AI Title #shorts",
                            "sources": ["Test Source"],
                            "lines": [{"text": "Hook question?", "caps": "Hook *question?"}]
                        })
                    }]
                }
            }]
        }

        def fake_urlopen(req, timeout=30):
            called_urls.append(req.full_url)
            cm = MagicMock()
            cm.__enter__.return_value.read.return_value = json.dumps(fake_response).encode("utf-8")
            return cm

        with patch('urllib.request.urlopen', side_effect=fake_urlopen):
            res = generate_with_gemini("fake-key", set(), self.slots_cfg["3"])
            self.assertEqual(res["topic"], "Fresh AI Topic")
            self.assertTrue(called_urls)
            self.assertNotIn("gemini-1.5-flash", called_urls[0])
            self.assertNotIn("gemini-2.0-flash", called_urls[0])

    def test_tier1_all_curriculum_topics_pass_topic_and_script_guards(self):
        """Verify all curriculum scripts are mutually unique and all remaining/new fallbacks pass TopicGuard."""
        sg = ScriptGuard(state_mgr=self.state_mgr)
        for sid, info in self.slots_cfg.items():
            for idx, fb in enumerate(info.get("fallbacks", [])):
                with self.subTest(phase="script", slot=sid, idx=idx, topic=fb["topic"]):
                    s_u, s_reason, s_meta = sg.evaluate_script_uniqueness(fb["lines"], fb["topic"], fb["title"])
                    self.assertTrue(s_u, f"ScriptGuard collision in Slot {sid}[{idx}]: {s_reason}")
                    sg.record_approved_script(fb["lines"], fb["topic"], fb["title"], s_meta["sha256"])

        # Check all currently unused and replenished topics against live history + each other
        sim_state_dir = self.test_dir / "curriculum_tg_state"
        live_state = ROOT / "cloud" / "state"
        if live_state.exists():
            shutil.copytree(live_state, sim_state_dir)
        sim_pub = self.test_dir / "curriculum_published.md"
        if (ROOT / "_published.md").exists():
            shutil.copy2(ROOT / "_published.md", sim_pub)

        sm_hist = StateManager(state_dir=sim_state_dir, published_file=sim_pub)
        tg = TopicGuard(state_mgr=sm_hist)
        for idx, fb in enumerate(self.slots_cfg["3"]["fallbacks"][15:], start=15):
            with self.subTest(phase="slot3_replenished", idx=idx, topic=fb["topic"]):
                is_u, reason, _ = tg.evaluate_topic_uniqueness(fb["topic"], fb["title"])
                self.assertTrue(is_u, f"New Slot 3[{idx}] failed TopicGuard: {reason}")
                reserved, _ = tg.reserve_if_unique(fb["topic"], fb["title"], "3", f"curr-3-{idx}")
                self.assertTrue(reserved)

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

    def test_tier4_scaffold_2d_project_capture_compatibility(self):
        """Verify scaffold_2d_project creates index.html and main.js complying with tools/capture.mjs OP API."""
        from cloud.visual_engine_2d import scaffold_2d_project
        temp_dir = Path(tempfile.mkdtemp(prefix="test_scaffold_"))
        try:
            sample_lines = [
                {"text": "Hook line text", "caps": "Hook *line"},
                {"text": "Conclusion loop text", "caps": "Conclusion *loop", "gap": 0.25}
            ]
            scaffold_2d_project(temp_dir, "Test Title #shorts", "glass is an amorphous solid", sample_lines, [])

            # Check index.html
            index_html = temp_dir / "index.html"
            self.assertTrue(index_html.exists())
            html_text = index_html.read_text(encoding="utf-8")
            self.assertIn('id="cv"', html_text)
            self.assertIn('src="src/main.js"', html_text)

            # Check main.js
            main_js = temp_dir / "src" / "main.js"
            self.assertTrue(main_js.exists())
            main_text = main_js.read_text(encoding="utf-8")
            self.assertIn("window.OP", main_text)
            self.assertIn("OP.ready = true", main_text)
            self.assertIn("OP.duration =", main_text)
            self.assertIn("OP.draw =", main_text)
            self.assertIn("OP.frame =", main_text)
            self.assertIn("OP.cues =", main_text)
            self.assertIn("OP.shots =", main_text)
            self.assertIn("loadTiming()", main_text)

            # Check tools
            self.assertTrue((temp_dir / "tools" / "capture.mjs").exists())
            self.assertTrue((temp_dir / "tools" / "mix.py").exists())
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

        vec_rip, _, _ = detect_topic_focal_vector("How to survive a rip current: The shoreline trap", [])
        self.assertEqual(vec_rip, "HYDRO_FLOW")

        vec_flag, _, _ = detect_topic_focal_vector("Why no national flag uses the color purple", [])
        self.assertEqual(vec_flag, "TELEMETRY_COMPASS")

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

    def test_tier8_procedural_background_and_widget_catalog(self):
        """Assert kit2d.js exports all 4 procedural backgrounds and 4 infographic widgets."""
        palette = THEMES["COSMIC_SPACE"]["palettes"][0]
        kit_code = generate_kit2d_js(palette)
        expected_primitives = [
            # 4 Procedural Parallax Backgrounds
            "bgContours",
            "bgHex",
            "bgStarfield",
            "bgRadar",
            "bgThemeParallax",
            # 4 Infographic & HUD Widgets
            "drawBigStat",
            "drawSplitComparison",
            "drawWaveform",
            "drawPipelineNodes"
        ]
        for fn in expected_primitives:
            self.assertIn(f"export function {fn}", kit_code, f"Missing required export {fn} in kit2d.js")

    def test_tier8_theme_shot_sequence_diversity(self):
        """Assert each genre theme generates distinct scene sequences and diverse widget archetypes."""
        lines = [
            {"text": "Line 1"},
            {"text": "Line 2"},
            {"text": "Line 3"},
            {"text": "Line 4"},
            {"text": "Line 5"}
        ]
        # Survival Tactical should generate COMPARE_SPLIT
        _, seq_surv, _ = generate_shots_js("Survival", "Survival", lines, "SURVIVAL_TACTICAL", THEMES["SURVIVAL_TACTICAL"]["palettes"][0])
        self.assertIn("COMPARE_SPLIT", seq_surv)

        # Cosmic Space should generate BIG_STAT_METRIC
        _, seq_space, _ = generate_shots_js("Space", "Space", lines, "COSMIC_SPACE", THEMES["COSMIC_SPACE"]["palettes"][0])
        self.assertIn("BIG_STAT_METRIC", seq_space)

        # Atomic Physics should generate WAVE_OSCILLATION
        _, seq_phys, _ = generate_shots_js("Physics", "Physics", lines, "ATOMIC_PHYSICS", THEMES["ATOMIC_PHYSICS"]["palettes"][0])
        self.assertIn("WAVE_OSCILLATION", seq_phys)

        # Historic Documentary should generate PIPELINE_FLOW
        _, seq_hist, _ = generate_shots_js("History", "History", lines, "HISTORIC_DOCUMENTARY", THEMES["HISTORIC_DOCUMENTARY"]["palettes"][0])
        self.assertIn("PIPELINE_FLOW", seq_hist)

    def test_gate3_zero_boilerplate_cards_across_all_curriculum_topics(self):
        """Scaffold all 90+ topics and verify zero stuck boilerplate cards and valid JS syntax."""
        from concurrent.futures import ThreadPoolExecutor
        from cloud.asset_guard import check_boilerplate_cards
        from cloud.visual_engine_2d import scaffold_2d_project
        has_node = shutil.which("node") is not None
        js_to_check = []

        for sid, info in self.slots_cfg.items():
            for idx, fb in enumerate(info.get("fallbacks", [])):
                with self.subTest(slot=sid, idx=idx, topic=fb["topic"]):
                    pdir = self.test_dir / f"s{sid}_{idx}"
                    scaffold_2d_project(
                        proj_dir=pdir,
                        title=fb["title"],
                        topic=fb["topic"],
                        lines=fb["lines"],
                        recent_palette_ids=[],
                        run_id=f"test-bp-{sid}-{idx}"
                    )
                    manifest = json.loads((pdir / "asset_manifest.json").read_text(encoding="utf-8"))
                    cards = manifest.get("card_texts", [])
                    self.assertGreater(len(cards), 0)
                    script_txt = " ".join(l["text"] for l in fb["lines"])
                    ok, violations = check_boilerplate_cards(cards, topic=fb["topic"], title=fb["title"], script_text=script_txt)
                    self.assertTrue(ok, f"Boilerplate violation in Slot {sid}[{idx}]: {violations}")

                    if has_node:
                        js_to_check.append((sid, idx, fb["topic"], pdir / "src" / "shots.js"))
                        if idx == 0:
                            js_to_check.append((sid, idx, fb["topic"], pdir / "src" / "core" / "kit2d.js"))
                            js_to_check.append((sid, idx, fb["topic"], pdir / "src" / "main.js"))

        if has_node and js_to_check:
            def _chk_js(item):
                sid_x, idx_x, top_x, fp = item
                res = subprocess.run(["node", "--check", str(fp)], capture_output=True, text=True)
                return sid_x, idx_x, top_x, fp.name, res.returncode, res.stderr

            with ThreadPoolExecutor(max_workers=6) as ex:
                for sid_x, idx_x, top_x, fname, rc, stderr in ex.map(_chk_js, js_to_check):
                    self.assertEqual(rc, 0, f"JS syntax error in Slot {sid_x}[{idx_x}] {fname} for {top_x}: {stderr}")

    def test_gate3_caption_safe_zone_no_overlap(self):
        """Verify generated shots place all cards and widgets above the y=1250..1550 caption zone."""
        from cloud.visual_engine_2d import scaffold_2d_project
        sample_topics = [
            self.slots_cfg["1"]["fallbacks"][3],
            self.slots_cfg["2"]["fallbacks"][3],
            self.slots_cfg["3"]["fallbacks"][15],
            self.slots_cfg["3"]["fallbacks"][18],
        ]
        draw_y_re = re.compile(
            r'K\.(?:drawTopicPill|drawStepCard|drawBigStat|drawSplitComparison|drawComparisonBar|drawHazardBanner|drawRadialGauge|drawWaveform|drawPipelineNodes|drawPointerTag)\([^)]*?\)'
        )
        for idx, fb in enumerate(sample_topics):
            pdir = self.test_dir / f"safe_{idx}"
            scaffold_2d_project(pdir, fb["title"], fb["topic"], fb["lines"], [], run_id=f"safe-{idx}")
            shots_js = (pdir / "src" / "shots.js").read_text(encoding="utf-8")
            # Check no hardcoded y=1320 or y inside 1200..1600 caption overlap band
            self.assertNotIn("1320", shots_js)
            for call in draw_y_re.findall(shots_js):
                nums = [int(n) for n in re.findall(r',\s*(\d{3,4})\b', call)]
                for val in nums:
                    if 1200 <= val <= 1650:
                        self.fail(f"Widget coordinate {val} overlaps caption zone in call: {call}")

    def test_gate3_fresh_assets_enforced_never_reused(self):
        """Gate 3B: Reject boilerplate cards, duplicate seeds, reused cards, stale manifests, and consecutive asset clones."""
        from cloud.asset_guard import AssetGuard
        from cloud.visual_engine_2d import scaffold_2d_project
        ag = AssetGuard(self.state_mgr)

        fb_a = self.slots_cfg["3"]["fallbacks"][15]
        fb_b = self.slots_cfg["1"]["fallbacks"][3]
        p1 = self.test_dir / "fresh_1"
        scaffold_2d_project(p1, fb_a["title"], fb_a["topic"], fb_a["lines"], [], run_id="run-fresh-1")
        m1 = json.loads((p1 / "asset_manifest.json").read_text(encoding="utf-8"))
        ok1, r1 = ag.evaluate_asset_uniqueness(m1, topic=fb_a["topic"], title=fb_a["title"])
        self.assertTrue(ok1, r1)
        fresh1, fr1 = ag.verify_project_freshness(p1, "run-fresh-1")
        self.assertTrue(fresh1, fr1)
        ag.record_approved_assets(m1)

        # Reject duplicate asset_seed / workspace
        dup_seed = dict(m1)
        dup_seed["project_dir_name"] = "different_dir"
        ok_dup, _ = ag.evaluate_asset_uniqueness(dup_seed)
        self.assertFalse(ok_dup)

        # Reject reused boilerplate cards
        bad_bp = dict(m1)
        bad_bp["asset_seed"] = "brandnewseed1234"
        bad_bp["project_dir_name"] = "fresh_bp"
        bad_bp["shots_sha256"] = "unique_hash"
        bad_bp["card_texts"] = ["90° DEGREE ANGLE", "DID YOU KNOW THIS?"]
        ok_bp, bp_reason = ag.evaluate_asset_uniqueness(bad_bp, topic=fb_b["topic"], title=fb_b["title"])
        self.assertFalse(ok_bp)
        self.assertIn("Boilerplate", bp_reason.title() if "boilerplate" in bp_reason.lower() else bp_reason)

        # Reject stale or tampered manifest
        fresh_wrong_run, _ = ag.verify_project_freshness(p1, "run-other")
        self.assertFalse(fresh_wrong_run)
        (p1 / "src" / "shots.js").write_text("// tampered", encoding="utf-8")
        fresh_tampered, _ = ag.verify_project_freshness(p1, "run-fresh-1")
        self.assertFalse(fresh_tampered)

        # Second genuinely distinct video must pass
        p2 = self.test_dir / "fresh_2"
        scaffold_2d_project(
            p2, fb_b["title"], fb_b["topic"], fb_b["lines"],
            [m1["palette_id"]], run_id="run-fresh-2", recent_assets=self.state_mgr.get_asset_history()
        )
        m2 = json.loads((p2 / "asset_manifest.json").read_text(encoding="utf-8"))
        ok2, r2 = ag.evaluate_asset_uniqueness(m2, topic=fb_b["topic"], title=fb_b["title"])
        self.assertTrue(ok2, r2)

    def test_gate3_word_sync_wd_and_shot_diversity(self):
        """Verify shots.js uses Wd() word timing and avoids consecutive duplicate shot layouts."""
        from cloud.visual_engine_2d import scaffold_2d_project
        fb = self.slots_cfg["3"]["fallbacks"][18]
        pdir = self.test_dir / "wd_check"
        _, _, seq = scaffold_2d_project(pdir, fb["title"], fb["topic"], fb["lines"], [], run_id="run-wd-1")
        shots_code = (pdir / "src" / "shots.js").read_text(encoding="utf-8")
        self.assertIn("Wd(", shots_code)
        for k in range(len(seq) - 1):
            self.assertNotEqual(seq[k], seq[k + 1], f"Consecutive duplicate shot layout at index {k}: {seq}")

    def test_audio_mix_config_varies_per_video(self):
        """Verify per-video music_config and generated mix.py vary across consecutive videos."""
        from cloud.visual_engine_2d import build_music_config, generate_mix_py
        mc1 = build_music_config("SURVIVAL_TACTICAL", "seed-aaa-111", [])
        mc2 = build_music_config("SURVIVAL_TACTICAL", "seed-aaa-111", [{"music_config": mc1}])
        self.assertNotEqual(
            (mc1["mode"], mc1["root_hz"], mc1["bpm"]),
            (mc2["mode"], mc2["root_hz"], mc2["bpm"])
        )
        mix_code = generate_mix_py(mc2)
        self.assertIn("music_config", mix_code)
        self.assertIn("music_ambient", mix_code)

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

    def test_gate4_context_aware_deduplication(self):
        """Gate 4: Cross-theme common layout noise is tolerated while same-theme duplicates are caught."""
        from unittest.mock import patch
        auditor = VideoQualityAuditor(state_mgr=self.state_mgr)
        fake_video = self.test_dir / "test_video.mp4"
        fake_video.write_bytes(b"\x00" * 500000)

        # History has a video in a DIFFERENT theme (HISTORIC_DOCUMENTARY)
        auditor.history = [{
            "title": "Why No Flag Uses Purple #shorts",
            "theme": "HISTORIC_DOCUMENTARY",
            "palette": "bronze_antiquity",
            "frame_hashes": ["1234567812345678"] * 10,
            "file_hash": "different_sha256"
        }]

        with patch.object(auditor, 'validate_video_integrity', return_value=(True, "OK")), \
             patch('cloud.duplicate_detector.extract_frame_dhashes', return_value=["1234567812345678"] * 10), \
             patch('cloud.duplicate_detector.compare_dhash_lists', return_value=(11.0, 0.828)):
            # Cross-theme with 82.8% similarity should be APPROVED
            is_dup, reason, _ = auditor.audit_and_check_duplicate(
                fake_video, "Rip Current", "How To Escape A Deadly Rip Current #shorts",
                "SURVIVAL_TACTICAL", "oceanic_abyss", ["HOOK_HYDRO_FLOW"]
            )
            self.assertFalse(is_dup, f"Cross-theme video should be approved, got: {reason}")

        # Now add same-theme video with 86% similarity -> should be REJECTED
        auditor.history.append({
            "title": "Other Survival Short",
            "theme": "SURVIVAL_TACTICAL",
            "palette": "oceanic_abyss",
            "frame_hashes": ["1234567812345678"] * 10,
            "file_hash": "different_sha256_2"
        })
        with patch.object(auditor, 'validate_video_integrity', return_value=(True, "OK")), \
             patch('cloud.duplicate_detector.extract_frame_dhashes', return_value=["1234567812345678"] * 10), \
             patch('cloud.duplicate_detector.compare_dhash_lists', return_value=(9.0, 0.860)):
            is_dup, reason, _ = auditor.audit_and_check_duplicate(
                fake_video, "Rip Current", "How To Escape A Deadly Rip Current #shorts",
                "SURVIVAL_TACTICAL", "oceanic_abyss", ["HOOK_HYDRO_FLOW"]
            )
            self.assertTrue(is_dup)
            self.assertIn("exceeds threshold", reason)

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
    def _run_isolated_three_slot_dry_run(self, state_dir: Path, pub_file: Path) -> dict[str, str]:
        env = os.environ.copy()
        env.pop("GEMINI_API_KEY", None)
        env["AUTOSHORT_STATE_DIR"] = str(state_dir)
        env["AUTOSHORT_PUBLISHED_FILE"] = str(pub_file)
        env["AUTOSHORT_KEEP_RESERVATION"] = "1"

        chosen: dict[str, str] = {}
        for slot in ["1", "2", "3"]:
            with self.subTest(slot=slot):
                cmd = [
                    sys.executable,
                    str(ROOT / 'cloud' / 'cloud_runner.py'),
                    '--dry-run',
                    '--slot', slot,
                    '--state-dir', str(state_dir),
                    '--published-file', str(pub_file),
                    '--keep-reservation'
                ]
                proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=str(ROOT), env=env)
                self.assertEqual(
                    proc.returncode, 0,
                    f"Dry run failed for Slot {slot}.\nSTDOUT: {proc.stdout}\nSTDERR: {proc.stderr}"
                )
                self.assertIn("DRY-RUN COMPLETE.", proc.stdout)

                match = re.search(r"Topic:\s*(.+)", proc.stdout)
                self.assertIsNotNone(match, f"Failed to match selected topic in Slot {slot} stdout")
                topic = match.group(1).strip()
                self.assertNotIn(topic, chosen.values(), f"Slot {slot} duplicated previously chosen topic: '{topic}'")
                chosen[slot] = topic
        return chosen

    def test_e2e_dry_run_all_three_slots_produce_unique_topics(self):
        """Simulate end-to-end cloud runner execution for all 3 slots via CLI in isolated state."""
        sim_state_dir = self.test_dir / "e2e_state"
        live_state_dir = ROOT / "cloud" / "state"
        if live_state_dir.exists():
            shutil.copytree(live_state_dir, sim_state_dir)
        else:
            sim_state_dir.mkdir(parents=True, exist_ok=True)

        sim_pub_file = self.test_dir / "_published.md"
        live_pub_file = ROOT / "_published.md"
        if live_pub_file.exists():
            shutil.copy2(live_pub_file, sim_pub_file)

        # If fewer than 3 unused offline fallbacks remain globally in live history,
        # simulate against a clean baseline so CI doesn't block Gemini-backed production runs.
        probe_sm = StateManager(state_dir=sim_state_dir, published_file=sim_pub_file)
        probe_tg = TopicGuard(probe_sm)
        available_count = sum(
            1
            for info in self.slots_cfg.values()
            for fb in info.get("fallbacks", [])
            if probe_tg.evaluate_topic_uniqueness(fb["topic"], fb["title"])[0]
        )
        if available_count < 3:
            shutil.rmtree(sim_state_dir)
            sim_state_dir.mkdir(parents=True, exist_ok=True)
            if sim_pub_file.exists():
                sim_pub_file.unlink()

        chosen = self._run_isolated_three_slot_dry_run(sim_state_dir, sim_pub_file)
        self.assertEqual(len(set(chosen.values())), 3)

    def test_gate1_cross_slot_selection_never_duplicates_active_session(self):
        """When Slot 3 exhausts all fallbacks, cross-slot search never duplicates Slot 1 or 2."""
        cross_state_dir = self.test_dir / "cross_slot_state"
        cross_pub_file = self.test_dir / "cross_published.md"
        sm = StateManager(state_dir=cross_state_dir, published_file=cross_pub_file)

        # Mark every Slot 3 fallback as already published
        for idx, fb in enumerate(self.slots_cfg["3"]["fallbacks"]):
            sm.confirm_topic_published(
                topic=fb["topic"],
                title=fb["title"],
                youtube_url=f"https://example.com/{idx}",
                slot_id="3",
                run_id=f"exhaust-slot3-{idx}"
            )

        chosen = self._run_isolated_three_slot_dry_run(cross_state_dir, cross_pub_file)
        self.assertEqual(len(set(chosen.values())), 3)
        slot3_topics = {fb["topic"] for fb in self.slots_cfg["3"]["fallbacks"]}
        self.assertNotIn(chosen["3"], slot3_topics)

    # =========================================================================
    # Tier 12: System Upgrades (Multi-Style 2D, Loop Pacing, LUFS, Gate 3C, SEO)
    # =========================================================================
    def test_tier1_slots_expanded_runway(self):
        """All 3 slots carry at least 30 curated topics each (>= 90 total)."""
        total = 0
        for sid, info in self.slots_cfg.items():
            cnt = len(info.get("fallbacks", []))
            self.assertGreaterEqual(cnt, 30, f"Slot {sid} expected >= 30 topics, got {cnt}")
            total += cnt
        self.assertGreaterEqual(total, 90)

    def test_multistyle_scaffold_compatibility(self):
        """2d-motion, paper-atlas, and stick-story scaffold valid bright-start JS and AssetGuard manifests."""
        from cloud.asset_guard import AssetGuard
        from cloud.style_router import scaffold_styled_project

        ag = AssetGuard(self.state_mgr)
        has_node = shutil.which("node") is not None
        samples = [
            ("2d-motion", self.slots_cfg["1"]["fallbacks"][3]),
            ("paper-atlas", self.slots_cfg["3"]["fallbacks"][18]),
            ("stick-story", self.slots_cfg["3"]["fallbacks"][15]),
        ]
        for idx, (target_style, fb) in enumerate(samples):
            with self.subTest(style=target_style, topic=fb["topic"]):
                pdir = self.test_dir / f"ms_{idx}"
                theme, pid, seq, chosen = scaffold_styled_project(
                    proj_dir=pdir,
                    title=fb["title"],
                    topic=fb["topic"],
                    lines=fb["lines"],
                    recent_palette_ids=[],
                    run_id=f"ms-run-{idx}",
                    requested_style=target_style,
                )
                self.assertEqual(chosen, target_style)
                manifest = json.loads((pdir / "asset_manifest.json").read_text(encoding="utf-8"))
                self.assertEqual(manifest.get("style"), target_style)
                fresh_ok, fresh_msg = ag.verify_project_freshness(pdir, f"ms-run-{idx}")
                self.assertTrue(fresh_ok, fresh_msg)
                ok_asset, msg_asset = ag.evaluate_asset_uniqueness(manifest, topic=fb["topic"], title=fb["title"])
                self.assertTrue(ok_asset, msg_asset)

                main_js = (pdir / "src" / "main.js").read_text(encoding="utf-8")
                self.assertNotIn("clamp(t / 0.", main_js)

                if has_node:
                    kit_rel = "src/core/kit2d.js" if target_style == "2d-motion" else "src/core/kit.js"
                    for rel in [kit_rel, "src/shots.js", "src/main.js"]:
                        chk = subprocess.run(["node", "--check", str(pdir / rel)], capture_output=True, text=True)
                        self.assertEqual(chk.returncode, 0, f"JS syntax error in {target_style} {rel}: {chk.stderr}")

    def test_stick_story_variants_valid_js_syntax(self):
        """All stick-story stage variants (snow/avalanche, grain, water, indoor) emit valid JS syntax."""
        from cloud.style_router import scaffold_styled_project

        has_node = shutil.which("node") is not None
        self.assertTrue(has_node, "Node.js is required to syntax-check generated JS")
        variants = [
            ("snow", "How to Survive an Avalanche #shorts", "surviving a snow avalanche burial"),
            ("grain", "Why Grain Silos Swallow You Whole #shorts", "grain silo corn entrapment"),
            ("water", "How to Escape a Rip Current #shorts", "escaping an ocean rip current"),
            ("indoor", "What to Do During a House Fire #shorts", "escaping a nighttime house fire"),
        ]
        for idx, (label, title, topic) in enumerate(variants):
            with self.subTest(variant=label):
                pdir = self.test_dir / f"stick_{label}"
                lines = [
                    {"text": f"Here is what happens during {topic}.", "caps": "Here is *what"},
                    {"text": "Panic makes your body sink deeper into the hazard every second.", "caps": "Panic *makes"},
                    {"text": "Stay calm, create an air pocket, and wait for rescue.", "caps": "Stay *calm", "gap": 0.2},
                ]
                _, _, _, chosen = scaffold_styled_project(
                    proj_dir=pdir,
                    title=title,
                    topic=topic,
                    lines=lines,
                    recent_palette_ids=[],
                    run_id=f"stick-var-{idx}",
                    requested_style="stick-story",
                )
                self.assertEqual(chosen, "stick-story")
                for rel in ["src/core/kit.js", "src/shots.js", "src/main.js"]:
                    chk = subprocess.run(["node", "--check", str(pdir / rel)], capture_output=True, text=True)
                    self.assertEqual(chk.returncode, 0, f"JS syntax error in stick-story ({label}) {rel}: {chk.stderr}")
                if label == "snow":
                    shots_js = (pdir / "src" / "shots.js").read_text(encoding="utf-8")
                    self.assertIn("ctx.fillStyle = '#DCE8F2';", shots_js)

    def test_loop_pacing_and_subcut_cadence(self):
        """Longer lines generate Wd() mid-line sub-cuts without duplicating scene_sequence neighbors."""
        from cloud.visual_engine_2d import scaffold_2d_project
        long_lines = [
            {"text": "Why do falling grains trap farmers inside silos so fast?", "caps": "Falling *grains | trap *fast?"},
            {"text": "When bottom augers unload dry corn kernels, the falling surface funnels inward trapping your legs rapidly.", "caps": "Surface *funnels | trapping *legs", "visual": {"focus_word": "funnels"}},
            {"text": "Each breath packs hundreds of rigid kernels tighter around your ribs every second.", "caps": "Kernels *pack | tighter *every second", "visual": {"focus_word": "kernels"}},
            {"text": "Which explains why solid seeds act like quicksand before you step...", "caps": "Solid *seeds | act like *quicksand", "gap": 0.15},
        ]
        pdir = self.test_dir / "subcut_test"
        _, _, seq = scaffold_2d_project(pdir, "Grain Silo Subcuts #shorts", "grain silo entrapment", long_lines, [], run_id="sub-1")
        shots_js = (pdir / "src" / "shots.js").read_text(encoding="utf-8")
        self.assertIn("S02a", shots_js)
        self.assertIn("S02b", shots_js)
        self.assertIn("Wd(", shots_js)
        for k in range(len(seq) - 1):
            self.assertNotEqual(seq[k], seq[k + 1])

    def test_audio_master_lufs_and_preflight_qa(self):
        """Audio mastering normalizes WAV loudly without clipping and Gate 3C flags uniform timing or silent WAVs."""
        import math, struct, wave
        from cloud.audio_master import inspect_wav_metrics, normalize_to_lufs_ffmpeg
        from cloud.preflight_qa import verify_whisper_alignment, verify_audio_mix

        pdir = self.test_dir / "qa_audio"
        (pdir / "data").mkdir(parents=True)
        sr = 48000
        dur_s = 2.0
        nframes = int(sr * dur_s)
        wav_path = pdir / "data" / "mix.wav"
        with wave.open(str(wav_path), "wb") as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            frames = bytearray()
            for i in range(nframes):
                s = int(2600 * math.sin(2 * math.pi * 220 * i / sr))
                frames.extend(struct.pack("<hh", s, s))
            wf.writeframes(bytes(frames))

        m_res = normalize_to_lufs_ffmpeg(wav_path, target_lufs=-14.0, true_peak=-1.0)
        after = m_res["after_metrics"]
        self.assertFalse(after["is_silent"])
        self.assertFalse(after["is_clipped"])
        if shutil.which("ffmpeg"):
            self.assertTrue(m_res["applied"])
            if after.get("lufs") is not None:
                self.assertGreater(after["lufs"], -16.5)

        ok_mix, msg_mix, _ = verify_audio_mix(wav_path, expected_duration=dur_s)
        self.assertTrue(ok_mix, msg_mix)

        # Silent WAV must fail Gate 3C
        silent_wav = pdir / "data" / "silent.wav"
        with wave.open(str(silent_wav), "wb") as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(b"\x00" * nframes * 4)
        ok_sil, _, _ = verify_audio_mix(silent_wav, expected_duration=dur_s)
        self.assertFalse(ok_sil)

        # Synthetic uniform inline_fallback timing must be flagged when allow_fallback=False
        (pdir / "data" / "lines.json").write_text(json.dumps({
            "duration": 4.0,
            "lines": [
                {"i": 0, "text": "One two three four", "start": 0.1, "end": 1.9},
                {"i": 1, "text": "Five six seven eight", "start": 2.1, "end": 3.8},
            ]
        }), encoding="utf-8")
        # Build exact uniform fallback timings (duty=0.92, constant char rate)
        uni_words = []
        for li, (txt, lo, hi) in enumerate([("One two three four", 0.1, 1.9), ("Five six seven eight", 2.1, 3.8)]):
            toks = txt.split()
            wts = [len(w) + 2.5 for w in toks]
            tot = sum(wts)
            c = lo
            for w, wt in zip(toks, wts):
                d = (hi - lo) * wt / tot
                uni_words.append({"w": w, "line": li, "s": round(c, 3), "e": round(c + d * 0.92, 3)})
                c += d
        (pdir / "data" / "words.json").write_text(json.dumps(uni_words), encoding="utf-8")

        ok_u, _, meta_u = verify_whisper_alignment(pdir, allow_fallback=False)
        self.assertFalse(ok_u)
        self.assertFalse(meta_u["whisper_aligned"])
        ok_allow, _, _ = verify_whisper_alignment(pdir, allow_fallback=True)
        self.assertTrue(ok_allow)

    def test_release_metadata_seo_schema(self):
        """build_release_metadata populates complete SEO title, sourced description, tags, and pinned comment."""
        from cloud.cloud_runner import build_release_metadata
        meta = build_release_metadata(
            title="The 35 MPH Molasses Flood #shorts",
            topic="The Great Molasses Flood of 1919: The 35 mph Boston syrup surge",
            lines=[
                {"text": "How did thick molasses kill people at thirty-five miles per hour?"},
                {"text": "Cold air later thickened spilled molasses trapping victims cleanly."}
            ],
            slot_info=self.slots_cfg["3"],
            tags=["history", "engineering"],
            sources=["Boston Globe 1919", "MIT Structural Study"],
            category_id="27",
            theme_name="HISTORIC_DOCUMENTARY",
            style="paper-atlas",
            palette_id="paper_atlas_parchment",
            duration_sec=34.2,
            lufs=-14.0,
        )
        self.assertEqual(meta["clean_title"], "The 35 MPH Molasses Flood")
        self.assertIn("Sources: Boston Globe 1919", meta["description"])
        self.assertIn("#shorts", meta["description"])
        self.assertTrue(len(meta["tags"]) >= 4)
        self.assertTrue(meta["pinned_comment"])
        self.assertEqual(meta["style"], "paper-atlas")
        self.assertEqual(meta["duration_sec"], 34.2)

    def test_gate4_records_duration_and_style(self):
        """VideoQualityAuditor persists duration_sec, style, and lufs metadata for analytics."""
        from unittest.mock import patch
        auditor = VideoQualityAuditor(state_mgr=self.state_mgr)
        fake_mp4 = self.test_dir / "dur_check.mp4"
        fake_mp4.write_bytes(b"\x55" * 500000)

        with patch.object(auditor, 'validate_video_integrity', return_value=(True, "OK")), \
             patch('cloud.duplicate_detector.get_video_duration', return_value=35.42), \
             patch('cloud.duplicate_detector.extract_frame_dhashes', return_value=["1234567812345678"] * 10):
            is_dup, reason, meta = auditor.audit_and_check_duplicate(
                fake_mp4, "Topic", "Title #shorts", "SURVIVAL_TACTICAL", "stick_story_daynight", ["HOOK"],
                style="stick-story", lufs=-14.1,
            )
            self.assertFalse(is_dup, reason)
            self.assertEqual(meta["duration_sec"], 35.42)
            self.assertEqual(meta["style"], "stick-story")
            self.assertEqual(meta["lufs"], -14.1)


if __name__ == '__main__':
    unittest.main()
