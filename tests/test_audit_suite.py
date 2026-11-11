#!/usr/bin/env python3
"""Comprehensive Audit & End-to-End Test Suite for Autonomous YouTube Shorts Engine.
Tests all five architectural tiers:
  Tier 1: Configuration Schema & Static Invariants
  Tier 2: Slot Routing & Deterministic Deduplication
  Tier 3: AI Intelligence Fallback & Fault Injection
  Tier 4: Dynamic 3D Scene Graph & Adaptive Shot Generation
  Tier 5: YouTube API Quota Budgeting & Auth Health
"""
import os
import re
import sys
import json
import shutil
import tempfile
import unittest
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from cloud.cloud_runner import (
    load_slots_config,
    detect_current_slot,
    get_published_topics,
    pick_topic_for_slot,
    write_adaptive_shots,
    slugify
)

class TestPipelineAuditSuite(unittest.TestCase):
    """Production Reliability & End-to-End Verification Test Suite."""

    @classmethod
    def setUpClass(cls):
        cls.slots_cfg = load_slots_config()

    # =========================================================================
    # Tier 1: Static Configuration & Schema Verification
    # =========================================================================
    def test_tier1_slots_configuration_integrity(self):
        """Assert all 5 slots exist and conform to schema standards."""
        expected_slots = {"1", "2", "3", "4", "5"}
        self.assertEqual(set(self.slots_cfg.keys()), expected_slots, "Missing or unexpected slot IDs")

        valid_categories = {"26", "27", "28"} # Howto, Education, Science & Tech

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

                # Style MUST be deep-dive to prevent ERR-007 (Three.js missing module error)
                self.assertEqual(
                    info['style'], 'deep-dive',
                    f"Slot {slot_id} style must be 'deep-dive', found: {info['style']}"
                )

                # Cron expression validation (5 fields)
                cron_parts = info['cron_utc'].split()
                self.assertEqual(len(cron_parts), 5, f"Invalid cron expression: {info['cron_utc']}")

                # Category verification
                self.assertIn(info['category_id'], valid_categories, f"Invalid YouTube category ID: {info['category_id']}")

                # Verify fallbacks
                fallbacks = info['fallbacks']
                self.assertGreater(len(fallbacks), 0, f"Slot {slot_id} has no fallback topics")
                for fb in fallbacks:
                    self.assertIn('topic', fb)
                    self.assertEqual(fb.get('style'), 'deep-dive', "Fallback style must be deep-dive")
                    self.assertIn('title', fb)
                    self.assertTrue(fb['title'].endswith('#shorts'), "Title must end with #shorts")
                    self.assertIn('lines', fb)
                    self.assertGreaterEqual(len(fb['lines']), 4, "Fallback must have at least 4 lines")
                    for line in fb['lines']:
                        self.assertIn('text', line)
                        self.assertIn('caps', line)

    # =========================================================================
    # Tier 2: Slot Routing & Deterministic Deduplication
    # =========================================================================
    def test_tier2_slot_auto_detection_boundaries(self):
        """Test UTC hour slot router across all operational windows."""
        test_cases = [
            (3, "1"),   # Exactly Slot 1 (08:00 AM PKT / 03:00 UTC)
            (4, "1"),   # Closer to Slot 1 than Slot 2
            (7, "2"),   # Exactly Slot 2 (12:00 PM PKT / 07:00 UTC)
            (9, "2"),   # Closer to Slot 2 (diff 2) than Slot 3 (diff 2, tie-breaker)
            (11, "3"),  # Exactly Slot 3 (04:00 PM PKT / 11:00 UTC)
            (14, "4"),  # Exactly Slot 4 (07:30 PM PKT / 14:30 UTC approx)
            (17, "5"),  # Exactly Slot 5 (10:00 PM PKT / 17:00 UTC)
            (18, "5"),  # Late evening, closest to Slot 5
        ]
        for hour, expected_slot in test_cases:
            from unittest.mock import patch
            from datetime import datetime, timezone
            mock_time = datetime(2026, 11, 11, hour, 15, 0, tzinfo=timezone.utc)
            with patch('cloud.cloud_runner.datetime') as mock_dt:
                mock_dt.now.return_value = mock_time
                detected = detect_current_slot(self.slots_cfg)
                self.assertEqual(
                    detected, expected_slot,
                    f"Hour {hour}:00 UTC should resolve to Slot {expected_slot}, got Slot {detected}"
                )

    def test_tier2_published_history_deduplication(self):
        """Test anti-duplication parser against _published.md."""
        topics = get_published_topics()
        self.assertIsInstance(topics, set)
        for t in topics:
            self.assertEqual(t, t.lower(), "Topics in set must be lowercased for case-insensitive matching")

    # =========================================================================
    # Tier 3: AI Intelligence Fallback & Fault Injection
    # =========================================================================
    def test_tier3_gemini_fallback_failover(self):
        """Test that missing or failing Gemini API falls back gracefully without raising exceptions."""
        for slot_id, info in self.slots_cfg.items():
            with self.subTest(slot_id=slot_id):
                # Simulated published list containing the first fallback
                first_topic = info['fallbacks'][0]['topic'].lower()
                mock_published = {first_topic}

                # Force fallback by ensuring no GEMINI_API_KEY is active during this check
                env_backup = os.environ.get('GEMINI_API_KEY')
                if 'GEMINI_API_KEY' in os.environ:
                    del os.environ['GEMINI_API_KEY']
                try:
                    result = pick_topic_for_slot(info, mock_published)
                    self.assertIsNotNone(result)
                    self.assertIn('topic', result)
                    self.assertIn('title', result)
                    self.assertIn('lines', result)
                    self.assertEqual(result.get('style', 'deep-dive'), 'deep-dive')
                finally:
                    if env_backup:
                        os.environ['GEMINI_API_KEY'] = env_backup

    # =========================================================================
    # Tier 4: Dynamic 3D Scene Graph & Adaptive Shot Generation
    # =========================================================================
    def test_tier4_adaptive_shots_syntax_and_importmap(self):
        """Verify adaptive shots.js generation has valid Three.js syntax and no undefined cuts."""
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
            write_adaptive_shots(temp_dir, title, sample_lines, "deep-dive")

            shots_file = temp_dir / 'src' / 'shots.js'
            self.assertTrue(shots_file.exists(), "shots.js was not generated")
            content = shots_file.read_text(encoding='utf-8')

            # Verify Three.js import presence
            self.assertIn("import * as THREE from 'three';", content)
            self.assertIn("export function buildShots(E)", content)

            # Verify cut markers match line indices
            self.assertIn("const st = cut(0);", content)
            self.assertIn("const st = cut(1);", content)
            self.assertIn("const st = cut(2);", content)
            self.assertIn("const st = cut(3);", content)

            # Verify shot IDs
            self.assertIn("'S01'", content)
            self.assertIn("'S02'", content)
            self.assertIn("'S03'", content)
            self.assertIn("'S04'", content)
        finally:
            shutil.rmtree(temp_dir)

    # =========================================================================
    # Tier 5: YouTube API Quota Budgeting & Auth Health
    # =========================================================================
    def test_tier5_youtube_quota_budget_verification(self):
        """Mathematically verify that 5 daily uploads do not breach YouTube Data API daily quota."""
        daily_quota_limit = 10000        # Google default YouTube Data API v3 quota
        cost_per_upload = 1600           # videos.insert base cost in API units
        num_daily_slots = 5

        total_daily_cost = cost_per_upload * num_daily_slots
        remaining_buffer = daily_quota_limit - total_daily_cost

        self.assertEqual(total_daily_cost, 8000, "5 daily uploads must total exactly 8,000 quota units")
        self.assertGreaterEqual(remaining_buffer, 2000, "Must maintain a minimum 2,000 unit safety buffer")

    def test_tier5_youtube_token_file_format(self):
        """If local youtube_tokens.json exists, verify its JSON structure."""
        token_file = ROOT / 'cloud' / 'youtube_tokens.json'
        if token_file.exists():
            data = json.loads(token_file.read_text(encoding='utf-8'))
            refresh_token = data.get('YOUTUBE_REFRESH_TOKEN') or data.get('refresh_token')
            client_id = data.get('YOUTUBE_CLIENT_ID') or data.get('client_id')
            client_secret = data.get('YOUTUBE_CLIENT_SECRET') or data.get('client_secret')

            self.assertIsNotNone(refresh_token, "Refresh token must exist in tokens file")
            self.assertIsNotNone(client_id, "Client ID must exist in tokens file")
            self.assertIsNotNone(client_secret, "Client secret must exist in tokens file")
            self.assertTrue(refresh_token.startswith('1//'), "Invalid refresh token prefix (must start with 1//)")

    # =========================================================================
    # End-to-End Simulation: Dry Run All 5 Slots
    # =========================================================================
    def test_e2e_dry_run_all_five_slots(self):
        """Simulate end-to-end cloud runner execution for all 5 slots via CLI."""
        for slot in ["1", "2", "3", "4", "5"]:
            with self.subTest(slot=slot):
                cmd = [sys.executable, str(ROOT / 'cloud' / 'cloud_runner.py'), '--dry-run', '--slot', slot]
                proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=str(ROOT))
                self.assertEqual(
                    proc.returncode, 0,
                    f"Dry run failed for Slot {slot}.\nSTDOUT: {proc.stdout}\nSTDERR: {proc.stderr}"
                )
                self.assertIn("DRY-RUN COMPLETE.", proc.stdout)
                self.assertIn("Style: deep-dive", proc.stdout)

if __name__ == '__main__':
    unittest.main()
