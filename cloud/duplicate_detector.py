#!/usr/bin/env python3
"""Duplicate Detection & Video Quality Control Engine (Gate 4).

Provides multi-tiered duplicate detection and pre-upload quality verification:
1. File SHA-256 fingerprinting.
2. 10-frame perceptual difference hashing (dHash) via FFmpeg raw stream extraction.
3. Blank/black frame filtering.
4. Normalized Hamming distance metrics and visual similarity against ALL historical entries.
5. Integration with Unified StateManager for atomic persistence.
6. Pre-upload container, resolution, duration, and audio stream integrity checks.
"""
from __future__ import annotations

import os
import sys
import json
import hashlib
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from cloud.state_manager import StateManager, get_state_manager

ROOT = Path(__file__).resolve().parent.parent
HISTORY_FILE = ROOT / "cloud" / "state" / "video_history.json"


def compute_file_sha256(path: Path) -> str:
    """Calculates SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def compute_dhash_from_grayscale_9x8(raw_bytes: bytes) -> str:
    """Computes a 64-bit difference hash (dHash) from 72 bytes (9x8 grayscale image).

    Each 8-pixel row produces 8 bits by comparing pixel[x] > pixel[x+1].
    Returns a 16-character hexadecimal string representing the 64-bit hash.
    """
    if len(raw_bytes) != 72:
        raise ValueError(f"Expected 72 raw bytes for 9x8 grayscale, got {len(raw_bytes)}")

    diff_bits = 0
    for row in range(8):
        row_offset = row * 9
        for col in range(8):
            left = raw_bytes[row_offset + col]
            right = raw_bytes[row_offset + col + 1]
            diff_bits = (diff_bits << 1) | (1 if left > right else 0)

    return f"{diff_bits:016x}"


def is_blank_or_solid_frame(raw_bytes: bytes) -> bool:
    """Detects if raw 9x8 grayscale frame is solid color (e.g. completely black or blank)."""
    if not raw_bytes or len(raw_bytes) < 72:
        return True
    first_byte = raw_bytes[0]
    # Check if all pixels are identical or variance is near zero
    diff = sum(abs(b - first_byte) for b in raw_bytes[:72])
    return diff < 15  # Solid black or solid gray


def hamming_distance(hex_hash1: str, hex_hash2: str) -> int:
    """Computes Hamming distance (differing bit count, 0-64) between two 64-bit hex hashes."""
    v1 = int(hex_hash1, 16)
    v2 = int(hex_hash2, 16)
    xor = v1 ^ v2
    return bin(xor).count("1")


def get_video_duration(video_path: Path) -> float:
    """Retrieves exact video duration in seconds using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video_path)
    ]
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, timeout=10)
        return float(out.decode("utf-8").strip())
    except Exception:
        return 0.0


def extract_frame_dhashes(video_path: Path, num_frames: int = 10) -> List[str]:
    """Extracts perceptual difference hashes at equidistant intervals across the video.

    Uses FFmpeg to stream 9x8 grayscale frames directly into Python.
    Filters out blank or unreadable frames.
    """
    duration = get_video_duration(video_path)
    if duration <= 0:
        duration = 30.0  # fallback default

    timestamps = [duration * (i + 1) / (num_frames + 1) for i in range(num_frames)]
    hashes = []

    for ts in timestamps:
        cmd = [
            "ffmpeg", "-v", "error",
            "-ss", f"{ts:.3f}",
            "-i", str(video_path),
            "-vframes", "1",
            "-vf", "scale=9:8,format=gray",
            "-f", "rawvideo",
            "-"
        ]
        try:
            raw_buf = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, timeout=15)
            if len(raw_buf) >= 72 and not is_blank_or_solid_frame(raw_buf[:72]):
                hashes.append(compute_dhash_from_grayscale_9x8(raw_buf[:72]))
            else:
                # If frame is blank or missing, use dummy indicator
                hashes.append("ffffffffffffffff")
        except Exception:
            hashes.append("ffffffffffffffff")

    return hashes


def compare_dhash_lists(hashes_a: List[str], hashes_b: List[str]) -> Tuple[float, float]:
    """Compares two lists of frame hashes.

    Returns:
        (avg_hamming_distance, similarity_ratio)
        where similarity_ratio is 1.0 (identical) down to 0.0 (completely dissimilar).
    """
    if not hashes_a or not hashes_b:
        return (64.0, 0.0)

    # Exclude dummy/failed frames from comparison
    valid_pairs = []
    n = min(len(hashes_a), len(hashes_b))
    for i in range(n):
        ha = hashes_a[i]
        hb = hashes_b[i]
        if ha != "ffffffffffffffff" and hb != "ffffffffffffffff":
            valid_pairs.append((ha, hb))

    if not valid_pairs:
        return (64.0, 0.0)

    distances = [hamming_distance(ha, hb) for ha, hb in valid_pairs]
    avg_dist = sum(distances) / len(valid_pairs)
    # 64 bits maximum distance. Similarity is normalized between 0.0 and 1.0
    similarity = max(0.0, 1.0 - (avg_dist / 64.0))
    return (avg_dist, similarity)


class VideoQualityAuditor:
    """Production Quality Control & Deduplication Engine (Gate 4)."""

    def __init__(self, state_mgr: Optional[StateManager] = None):
        self.state_mgr = state_mgr or get_state_manager()
        self.history = self.state_mgr.get_video_history()

    def validate_video_integrity(self, video_path: Path) -> Tuple[bool, str]:
        """Performs pre-upload structural validation on exported MP4."""
        if not video_path.exists():
            return False, f"File does not exist: {video_path}"

        file_size_mb = video_path.stat().st_size / (1024 * 1024)
        if file_size_mb < 0.4:
            return False, f"File size too small ({file_size_mb:.2f} MB), likely incomplete render."

        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "stream=codec_type,width,height:format=duration",
            "-of", "json",
            str(video_path)
        ]
        try:
            res = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, timeout=15)
            info = json.loads(res.decode("utf-8"))

            # Duration check
            duration = float(info.get("format", {}).get("duration", 0))
            if duration < 10.0:
                return False, f"Video duration too short ({duration:.1f}s), minimum is 10s."

            # Stream verification
            streams = info.get("streams", [])
            has_video = False
            has_audio = False
            correct_resolution = False

            for s in streams:
                if s.get("codec_type") == "video":
                    has_video = True
                    w, h = s.get("width"), s.get("height")
                    if (w, h) in [(1080, 1920), (720, 1280), (540, 960)]:
                        correct_resolution = True
                elif s.get("codec_type") == "audio":
                    has_audio = True

            if not has_video:
                return False, "Render contains no video stream."
            if not has_audio:
                return False, "Render contains no audio stream."
            if not correct_resolution:
                return False, "Video resolution does not match 9:16 portrait format."

            return True, "Integrity check passed."
        except Exception as e:
            return False, f"ffprobe validation failed: {e}"

    def audit_and_check_duplicate(
        self,
        video_path: Path,
        topic: str,
        title: str,
        theme: str,
        palette: str,
        scene_sequence: List[str],
        max_similarity_threshold: float = 0.78
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Evaluates whether candidate video is a visual or structural duplicate across all history.

        Returns:
            (is_duplicate, reason_message, metadata)
        """
        # 1. Structural file integrity check
        valid, msg = self.validate_video_integrity(video_path)
        if not valid:
            return True, f"Quality Rejection: {msg}", {}

        # 2. Compute exact file SHA-256
        file_hash = compute_file_sha256(video_path)

        # 3. Check exact file duplicates across ALL history
        for entry in self.history:
            if entry.get("file_hash") == file_hash:
                return True, f"Exact file duplicate detected (matches previously generated {entry.get('title')})", {}

        # 4. Extract 10 perceptual frame hashes
        frame_hashes = extract_frame_dhashes(video_path, num_frames=10)

        # 5. Check structural sequence against immediate predecessor
        if self.history:
            last_entry = self.history[-1]
            if (
                last_entry.get("theme") == theme and
                last_entry.get("palette") == palette and
                last_entry.get("scene_sequence") == scene_sequence
            ):
                return True, "Structural duplicate: Consecutive video cannot share identical theme, palette, and scene sequence.", {}

        # 6. Check perceptual similarity against ALL historical entries
        highest_similarity = 0.0
        most_similar_title = ""

        for entry in reversed(self.history):
            prev_hashes = entry.get("frame_hashes", [])
            if prev_hashes:
                _, sim = compare_dhash_lists(frame_hashes, prev_hashes)
                if sim > highest_similarity:
                    highest_similarity = sim
                    most_similar_title = entry.get("title", "Unknown")

        metadata = {
            "title": title,
            "topic": topic,
            "theme": theme,
            "palette": palette,
            "scene_sequence": scene_sequence,
            "file_hash": file_hash,
            "frame_hashes": frame_hashes,
            "similarity_score": round(highest_similarity, 3)
        }

        if highest_similarity >= max_similarity_threshold:
            return (
                True,
                f"Perceptual similarity {highest_similarity:.1%} exceeds threshold {max_similarity_threshold:.1%} (matches visual footage of '{most_similar_title}')",
                metadata
            )

        return False, f"Video approved. Max similarity score: {highest_similarity:.1%}", metadata

    def record_approved_video(self, metadata: Dict[str, Any]):
        """Records the newly approved video in persistent state."""
        self.state_mgr.record_video(metadata)
        self.history = self.state_mgr.get_video_history()
