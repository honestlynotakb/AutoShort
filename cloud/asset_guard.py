#!/usr/bin/env python3
"""Gate 3B Asset Provenance, Freshness, and Anti-Boilerplate Guard.

Enforces strict per-video asset creation rules:
1. Every video must generate fresh visual and audio assets in an isolated build folder.
2. No stuck/boilerplate template cards or labels may appear on screen.
3. Card labels, palettes, backgrounds, scene sequences, music parameters, and asset seeds
   must never be reused verbatim from prior videos.
4. Generated project files are verified against asset_manifest.json before rendering.
"""
from __future__ import annotations

import re
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from cloud.state_manager import StateManager, get_state_manager


# Generic filler / leftover template card phrases that are ALWAYS forbidden
ALWAYS_BANNED_CARDS: Set[str] = {
    "curious reality",
    "remember to look closer",
    "did you know this",
    "observe the difference",
    "observe the pattern",
    "crucial distinction",
    "key mechanism",
    "avoid the instinctive trap",
    "critical turning point",
    "surprising paradox",
    "scientific reality",
    "physical reality",
    "physical law",
    "physical ratio",
    "historical evidence",
    "recorded history",
    "scale of the universe",
    "astronomical scale",
    "gravitational tidal multiplier",
    "the point of no return",
    "cosmic boundary",
    "instantaneous phase shift",
    "atomic shatter threshold",
    "molecular level dynamics",
    "atomic oscillation",
    "common instinct",
    "fight resistance",
    "survival protocol",
    "90 degree angle",
    "90° degree angle",
    "signal flux",
}

# Domain-specific labels that are ONLY valid when their keywords actually exist in the script
CONTEXT_GATED_CARDS: Dict[str, Tuple[str, ...]] = {
    "roche limit": ("roche", "moon", "ring"),
    "critical event horizon": ("black hole", "event horizon", "singularity"),
    "seaward velocity: 8 ft/s": ("rip current", "eight feet"),
    "escape: 90° parallel": ("rip current", "parallel"),
    "bearing 240°": ("compass", "bearing", "navigation"),
    "hemispheric vector": ("compass", "hemispheric", "navigation"),
    "10,000x": ("10,000", "ten thousand"),
    "0.001s": ("0.001", "millisecond"),
    "99.9%": ("99.9",),
}


def normalize_card_text(text: str) -> str:
    """Normalizes card text for boilerplate and duplicate comparisons."""
    if not text:
        return ""
    clean = str(text).lower().strip()
    clean = re.sub(r'[?!.,;:"\'`]+', '', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean


def compute_asset_seed(run_id: str, topic: str, variant: int = 0) -> str:
    """Computes a deterministic per-run unique asset seed."""
    payload = f"{run_id}|{topic}|{variant}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:16]


def compute_text_sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def check_boilerplate_cards(
    card_texts: List[str],
    topic: str = "",
    title: str = "",
    script_text: str = ""
) -> Tuple[bool, List[str]]:
    """Checks all on-screen card/pill texts for banned boilerplate or irrelevant template leftovers."""
    violations: List[str] = []
    combined_ctx = f"{topic} {title} {script_text}".lower()

    normalized_set = {normalize_card_text(c) for c in card_texts if normalize_card_text(c)}

    # Catch generic 3-node fallback sequence when used verbatim
    if {"origin", "crucial pivot", "aftermath"}.issubset(normalized_set):
        violations.append("Generic 3-stage pipeline ('ORIGIN', 'CRUCIAL PIVOT', 'AFTERMATH')")

    for raw in card_texts:
        norm = normalize_card_text(raw)
        if not norm:
            continue
        if norm in ALWAYS_BANNED_CARDS:
            violations.append(f"Banned boilerplate card '{raw}'")
            continue
        for gated_phrase, required_terms in CONTEXT_GATED_CARDS.items():
            if norm == normalize_card_text(gated_phrase):
                if not any(term in combined_ctx for term in required_terms):
                    violations.append(f"Irrelevant template card '{raw}' (missing context {required_terms})")
    return len(violations) == 0, violations


class AssetGuard:
    """Gate 3B Auditor ensuring fresh, non-reused, topic-relevant visual and audio assets."""

    def __init__(self, state_mgr: Optional[StateManager] = None):
        self.state_mgr = state_mgr or get_state_manager()

    def evaluate_asset_uniqueness(
        self,
        manifest: Dict[str, Any],
        topic: str = "",
        title: str = "",
        script_text: str = ""
    ) -> Tuple[bool, str]:
        """Audits a planned/generated asset manifest for boilerplate and cross-video reuse."""
        asset_seed = manifest.get("asset_seed", "")
        if not asset_seed:
            return False, "Missing per-video asset_seed."

        card_texts = [str(c) for c in manifest.get("card_texts", []) if str(c).strip()]
        if not card_texts:
            return False, "Manifest contains no topic-specific card labels."

        bp_ok, bp_violations = check_boilerplate_cards(card_texts, topic=topic, title=title, script_text=script_text)
        if not bp_ok:
            return False, "; ".join(bp_violations)

        history = self.state_mgr.get_asset_history()
        if not history:
            return True, f"Fresh asset manifest verified (seed={asset_seed}, {len(card_texts)} unique labels)."

        curr_cards = {normalize_card_text(c) for c in card_texts if len(normalize_card_text(c)) >= 3}
        curr_palette = manifest.get("palette_id", "")
        curr_bgs = manifest.get("background_sequence", [])
        curr_scenes = manifest.get("scene_sequence", [])
        curr_theme = manifest.get("theme", "")
        curr_music = manifest.get("music_config", {})

        # Full-history checks for exact seed / directory / code fingerprint reuse
        for prev in history:
            if prev.get("asset_seed") == asset_seed:
                return False, f"Asset seed collision ({asset_seed}) with '{prev.get('title', 'Unknown')}'."
            if prev.get("project_dir_name") and prev.get("project_dir_name") == manifest.get("project_dir_name"):
                return False, f"Reused project workspace '{manifest.get('project_dir_name')}'."
            if prev.get("shots_sha256") and prev.get("shots_sha256") == manifest.get("shots_sha256"):
                return False, f"Identical shots.js generated as '{prev.get('title', 'Unknown')}'."

        # Check recent 10 videos for card label recycling and layout stagnation
        for prev in history[-10:]:
            prev_cards = {normalize_card_text(c) for c in prev.get("card_texts", []) if len(normalize_card_text(c)) >= 3}
            if curr_cards and prev_cards:
                overlap = curr_cards.intersection(prev_cards)
                union = curr_cards.union(prev_cards)
                jaccard = len(overlap) / len(union)
                if jaccard >= 0.45 or len(overlap) >= 3:
                    return (
                        False,
                        f"Reused on-screen card labels ({sorted(overlap)[:4]}) matching '{prev.get('title', 'Unknown')}'"
                    )

        # Immediate predecessor diversity checks
        last = history[-1]
        if (
            last.get("theme") == curr_theme and
            last.get("palette_id") == curr_palette and
            last.get("scene_sequence") == curr_scenes
        ):
            return False, f"Visual stagnation matching immediate predecessor ({curr_theme}, {curr_palette})."

        if curr_palette and last.get("palette_id") == curr_palette and curr_bgs and last.get("background_sequence") == curr_bgs:
            return False, f"Consecutive palette + background sequence reuse ({curr_palette})."

        last_music = last.get("music_config", {})
        if (
            curr_music and last_music and
            curr_music.get("mode") == last_music.get("mode") and
            curr_music.get("root_hz") == last_music.get("root_hz") and
            curr_music.get("bpm") == last_music.get("bpm")
        ):
            return False, "Audio music_config matches immediate predecessor (root_hz/bpm/mode must vary)."

        return True, f"Fresh per-video assets verified (seed={asset_seed}, palette={curr_palette})."

    def verify_project_freshness(self, proj_dir: Path, run_id: str) -> Tuple[bool, str]:
        """Verifies all scaffolded project files exist, belong to run_id, and match manifest hashes."""
        manifest_path = Path(proj_dir) / "asset_manifest.json"
        if not manifest_path.exists():
            return False, f"Missing asset_manifest.json in {proj_dir}"

        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as e:
            return False, f"Invalid asset_manifest.json: {e}"

        if manifest.get("run_id") != str(run_id):
            return False, f"Stale asset_manifest.json run_id={manifest.get('run_id')} != {run_id}"

        required_files = [
            "src/core/kit2d.js",
            "src/shots.js",
            "src/main.js",
            "tools/mix.py",
            "index.html",
        ]
        hashes = manifest.get("file_hashes", {})
        for rel in required_files:
            fp = Path(proj_dir) / rel
            if not fp.exists():
                return False, f"Missing freshly generated asset file: {rel}"
            actual_hash = compute_text_sha256(fp.read_text(encoding="utf-8"))
            expected_hash = hashes.get(rel)
            if expected_hash and actual_hash != expected_hash:
                return False, f"Asset integrity mismatch on {rel} (stale or tampered file)."

        return True, f"Verified {len(required_files)} fresh project assets for run {run_id}."

    def record_approved_assets(self, manifest: Dict[str, Any]):
        """Persists approved per-video asset provenance into asset_registry.json."""
        self.state_mgr.record_asset_manifest(manifest)
