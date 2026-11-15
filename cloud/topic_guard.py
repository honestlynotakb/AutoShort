#!/usr/bin/env python3
"""Semantic Topic Guard & Gate 1 Deduplication Engine.

Enforces strict semantic topic uniqueness before script generation:
1. Exact normalized string matching.
2. Case-insensitive and punctuation-stripped normalization.
3. Content word tokenization and stop-word filtering.
4. Jaccard token set similarity (threshold >= 0.55 rejected).
5. Character sequence similarity via SequenceMatcher (threshold >= 0.70 rejected).
6. Cross-checking against published, historical, and actively reserved topics.
"""

import re
import difflib
from typing import Dict, List, Optional, Set, Tuple, Any
from cloud.state_manager import StateManager, get_state_manager

# Common english and prompt stop words that dilute semantic comparison
STOP_WORDS: Set[str] = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "can't", "cannot", "could",
    "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down",
    "during", "each", "few", "for", "from", "further", "had", "hadn't", "has",
    "hasn't", "have", "haven't", "having", "he", "her", "here", "hers", "herself",
    "him", "himself", "his", "how", "i", "if", "in", "into", "is", "isn't", "it",
    "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my",
    "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other",
    "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "shan't",
    "she", "should", "shouldn't", "so", "some", "such", "than", "that", "the",
    "their", "theirs", "them", "themselves", "then", "there", "there's", "these",
    "they", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "wasn't", "we", "were", "weren't", "what", "what's", "when",
    "where", "which", "while", "who", "whom", "why", "with", "won't", "would",
    "wouldn't", "you", "your", "yours", "yourself", "yourselves",
    # YouTube and formatting stop words
    "shorts", "short", "video", "actually", "really", "happens", "happen", "happened",
    "would", "could", "inside", "truth", "behind", "know"
}


def normalize_text(text: str) -> str:
    """Removes punctuation, quotes, #shorts, and collapses whitespace."""
    if not text:
        return ""
    clean = text.lower()
    clean = re.sub(r'#shorts', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'[^\w\s]', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean


def extract_content_tokens(text: str) -> Set[str]:
    """Extracts informative content words, filtering out common stop words."""
    norm = normalize_text(text)
    words = norm.split()
    tokens = set()
    for w in words:
        if len(w) >= 3 and w not in STOP_WORDS:
            # Simple stemming for plural/verb forms
            if w.endswith("ies") and len(w) > 4:
                stem = w[:-3] + "y"
            elif w.endswith("ing") and len(w) > 4:
                stem = w[:-3]
            elif w.endswith("ed") and len(w) > 3:
                stem = w[:-2]
            elif w.endswith("es") and len(w) > 3:
                stem = w[:-2]
            elif w.endswith("s") and len(w) > 3:
                stem = w[:-1]
            else:
                stem = w
            tokens.add(stem)
    return tokens


def compute_jaccard_similarity(tokens_a: Set[str], tokens_b: Set[str]) -> float:
    """Computes Jaccard index between two token sets."""
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a.intersection(tokens_b)
    union = tokens_a.union(tokens_b)
    return len(intersection) / len(union)


def compute_sequence_similarity(text_a: str, text_b: str) -> float:
    """Computes character sequence similarity ratio via SequenceMatcher."""
    norm_a = normalize_text(text_a)
    norm_b = normalize_text(text_b)
    if not norm_a or not norm_b:
        return 0.0
    return difflib.SequenceMatcher(None, norm_a, norm_b).ratio()


class TopicGuard:
    """Gate 1 Topic Uniqueness Auditor."""

    def __init__(
        self,
        state_mgr: Optional[StateManager] = None,
        max_jaccard_threshold: float = 0.55,
        max_sequence_threshold: float = 0.70
    ):
        self.state_mgr = state_mgr or get_state_manager()
        self.max_jaccard = max_jaccard_threshold
        self.max_sequence = max_sequence_threshold

    def evaluate_topic_uniqueness(
        self,
        candidate_topic: str,
        candidate_title: str = ""
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Audits candidate topic against all published and reserved records.

        Returns:
            (is_unique, reason, matching_record)
        """
        candidate_norm = normalize_text(candidate_topic)
        candidate_title_norm = normalize_text(candidate_title)
        candidate_tokens = extract_content_tokens(candidate_topic)
        if candidate_title:
            candidate_tokens.update(extract_content_tokens(candidate_title))

        if not candidate_norm:
            return False, "Candidate topic is empty or invalid.", None

        # Retrieve active & historical records from state manager
        records = self.state_mgr.get_all_published_and_reserved_topics()

        # Pass 1: Exact normalized topic and title matching across all records
        for rec in records:
            prev_topic = rec.get("topic", "")
            prev_title = rec.get("title", "")
            prev_norm = normalize_text(prev_topic)
            prev_title_norm = normalize_text(prev_title)

            if candidate_norm == prev_norm:
                return False, f"Exact topic match with previously registered: '{prev_topic}'", rec
            if candidate_title_norm and prev_title_norm and candidate_title_norm == prev_title_norm:
                return False, f"Exact title match with previously registered: '{prev_title}'", rec

        # Pass 2: Semantic token overlap & character sequence similarity
        for rec in records:
            prev_topic = rec.get("topic", "")
            prev_title = rec.get("title", "")
            prev_tokens = extract_content_tokens(prev_topic)
            if prev_title:
                prev_tokens.update(extract_content_tokens(prev_title))

            jaccard = compute_jaccard_similarity(candidate_tokens, prev_tokens)
            if jaccard >= self.max_jaccard:
                overlap = list(candidate_tokens.intersection(prev_tokens))
                return (
                    False,
                    f"Semantic overlap: Jaccard similarity {jaccard:.2f} >= {self.max_jaccard:.2f} (shared keywords: {overlap}) with '{prev_topic}'",
                    rec
                )

            seq_sim = compute_sequence_similarity(candidate_topic, prev_topic)
            has_shared_token = bool(candidate_tokens.intersection(prev_tokens))
            if (seq_sim >= 0.85) or (seq_sim >= self.max_sequence and has_shared_token):
                return (
                    False,
                    f"Syntactic similarity: Sequence ratio {seq_sim:.2f} >= {self.max_sequence:.2f} with '{prev_topic}'",
                    rec
                )

        return True, "Topic passed all Gate 1 semantic uniqueness checks.", None

    def reserve_if_unique(
        self,
        candidate_topic: str,
        candidate_title: str,
        slot_id: str,
        run_id: str
    ) -> Tuple[bool, str]:
        """Atomically checks uniqueness and reserves topic for current run."""
        is_unique, reason, match = self.evaluate_topic_uniqueness(candidate_topic, candidate_title)
        if not is_unique:
            return False, reason

        reserved = self.state_mgr.reserve_topic(
            topic=candidate_topic,
            title=candidate_title,
            slot_id=str(slot_id),
            run_id=str(run_id)
        )
        if not reserved:
            return False, "Topic was concurrently reserved by another active run."

        return True, "Topic successfully verified and reserved."

    def build_gemini_rejection_constraint(self, rejected_topics: List[Tuple[str, str]]) -> str:
        """Constructs an explicit negative constraint prompt for subsequent Gemini retry attempts."""
        if not rejected_topics:
            return ""
        lines = ["\nCRITICAL NEGATIVE CONSTRAINTS (DO NOT REPEAT OR APPROXIMATE):"]
        for topic, reason in rejected_topics:
            lines.append(f" - REJECTED: \"{topic}\" (Reason: {reason})")
        lines.append("You MUST pick a COMPLETELY DISTINCT subject matter, mechanism, and physical reality.")
        return "\n".join(lines)
