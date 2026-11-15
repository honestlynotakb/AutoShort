#!/usr/bin/env python3
"""Script Narration Guard & Gate 2 Deduplication Engine.

Enforces narration uniqueness before neural voice synthesis:
1. Full script normalized SHA-256 fingerprinting.
2. Word 3-gram (tri-gram) Jaccard overlap checking against historical scripts (threshold >= 0.50 rejected).
3. Line-by-line sequence similarity to detect recycled scripts with superficial word edits.
4. Persistent registration into script_registry.json.
"""

import re
import hashlib
import difflib
from typing import Dict, List, Optional, Set, Tuple, Any
from cloud.state_manager import StateManager, get_state_manager


def normalize_script_text(text: str) -> str:
    """Normalizes script text for robust n-gram and fingerprint comparison."""
    if not text:
        return ""
    clean = text.lower()
    clean = re.sub(r'[^\w\s]', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean


def compute_script_sha256(script_text: str) -> str:
    """Calculates SHA-256 hash of normalized script text."""
    norm = normalize_script_text(script_text)
    return hashlib.sha256(norm.encode('utf-8')).hexdigest()


def extract_word_ngrams(text: str, n: int = 3) -> Set[str]:
    """Generates word n-grams (default tri-grams) from text."""
    norm = normalize_script_text(text)
    words = norm.split()
    if len(words) < n:
        return {" ".join(words)} if words else set()
    return {" ".join(words[i:i+n]) for i in range(len(words) - n + 1)}


def compute_ngram_jaccard(ngrams_a: Set[str], ngrams_b: Set[str]) -> float:
    """Calculates Jaccard overlap ratio between two n-gram sets."""
    if not ngrams_a or not ngrams_b:
        return 0.0
    return len(ngrams_a.intersection(ngrams_b)) / len(ngrams_a.union(ngrams_b))


class ScriptGuard:
    """Gate 2 Script Narration Uniqueness Auditor."""

    def __init__(
        self,
        state_mgr: Optional[StateManager] = None,
        max_ngram_threshold: float = 0.50,
        max_line_similarity: float = 0.85
    ):
        self.state_mgr = state_mgr or get_state_manager()
        self.max_ngram = max_ngram_threshold
        self.max_line_sim = max_line_similarity

    def compile_full_text(self, lines: List[Dict]) -> str:
        """Joins line texts into a single coherent narration string."""
        return " ".join([line.get("text", "").strip() for line in lines if line.get("text")])

    def evaluate_script_uniqueness(
        self,
        lines: List[Dict],
        topic: str,
        title: str
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Audits planned script lines against historical scripts.

        Returns:
            (is_unique, reason, metadata)
        """
        full_text = self.compile_full_text(lines)
        if not full_text:
            return False, "Candidate script is empty.", {}

        script_hash = compute_script_sha256(full_text)
        candidate_ngrams = extract_word_ngrams(full_text, n=3)

        historical = self.state_mgr.get_all_historical_scripts()

        for prev in historical:
            prev_hash = prev.get("sha256", "")
            prev_text = prev.get("full_text", "")
            prev_topic = prev.get("topic", "Unknown")

            # 1. Exact SHA-256 match
            if prev_hash and script_hash == prev_hash:
                return False, f"Exact script fingerprint match with historical script for '{prev_topic}'", {}

            # 2. Word 3-gram Jaccard overlap
            prev_ngrams = extract_word_ngrams(prev_text, n=3)
            overlap = compute_ngram_jaccard(candidate_ngrams, prev_ngrams)
            if overlap >= self.max_ngram:
                return (
                    False,
                    f"Substantial script overlap: 3-gram similarity {overlap:.1%} exceeds threshold {self.max_ngram:.1%} (matches '{prev_topic}')",
                    {}
                )

            # 3. Line-by-line similarity check for template recycling
            prev_lines = [l.strip() for l in prev_text.split(".") if l.strip()]
            reused_lines = 0
            for cl in lines:
                ct = cl.get("text", "").strip()
                for pl in prev_lines:
                    sim = difflib.SequenceMatcher(None, ct.lower(), pl.lower()).ratio()
                    if sim >= self.max_line_sim:
                        reused_lines += 1
                        break
            if reused_lines >= 3:
                return (
                    False,
                    f"Recycled script structure: {reused_lines} lines matched previous script for '{prev_topic}'",
                    {}
                )

        meta = {
            "sha256": script_hash,
            "full_text": full_text,
            "topic": topic,
            "title": title,
            "line_count": len(lines)
        }
        return True, "Script passed all Gate 2 originality checks.", meta

    def record_approved_script(self, lines: List[Dict], topic: str, title: str, script_hash: str):
        """Records script fingerprint into persistent registry."""
        full_text = self.compile_full_text(lines)
        self.state_mgr.record_script(
            script_text=full_text,
            topic=topic,
            title=title,
            lines=lines,
            script_hash=script_hash
        )
