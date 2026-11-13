#!/usr/bin/env python3
"""Duplicate Detection & Video Quality Control Engine.

Provides multi-tiered duplicate detection and pre-upload quality verification:
1. File SHA-256 fingerprinting.
2. Perceptual frame hashing (dHash) via FFmpeg raw stream extraction.
3. Visual similarity scoring & scene sequence comparison against historical uploads.
4. Pre-upload container, resolution, duration, and audio stream integrity checks.
"""

import os
import sys
import json
import hashlib
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple, Optional

ROOT = Path(__file__).resolve().parent.parent
HISTORY_FILE = ROOT / "cloud" / "video_history.json"

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

def extract_frame_dhashes(video_path: Path, num_frames: int = 5) -> List[str]:
    """Extracts perceptual difference hashes at equidistant intervals across the video.
    
    Uses FFmpeg to stream 9x8 grayscale frames directly into Python.
    Zero external heavy dependencies required.
    """
    duration = get_video_duration(video_path)
    if duration <= 0:
        duration = 30.0 # fallback default
        
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
            if len(raw_buf) >= 72:
                hashes.append(compute_dhash_from_grayscale_9x8(raw_buf[:72]))
            else:
                hashes.append("0000000000000000")
        except Exception:
            hashes.append("0000000000000000")
            
    return hashes

def compare_dhash_lists(hashes_a: List[str], hashes_b: List[str]) -> Tuple[float, float]:
    """Compares two lists of frame hashes.
    
    Returns:
        (avg_hamming_distance, similarity_ratio)
        where similarity_ratio is 1.0 (identical) down to 0.0 (completely dissimilar).
    """
    if not hashes_a or not hashes_b:
        return (64.0, 0.0)
        
    n = min(len(hashes_a), len(hashes_b))
    distances = [hamming_distance(hashes_a[i], hashes_b[i]) for i in range(n)]
    avg_dist = sum(distances) / n
    # Max distance is 64 bits. Distance of 0 = 100% similar, distance of 32 = ~50% similar
    similarity = max(0.0, 1.0 - (avg_dist / 64.0))
    return (avg_dist, similarity)

class VideoQualityAuditor:
    """Production Quality Control & Deduplication Engine."""
    
    def __init__(self, history_path: Optional[Path] = None):
        self.history_path = history_path or HISTORY_FILE
        self.history = self._load_history()
        
    def _load_history(self) -> List[Dict]:
        if not self.history_path.exists():
            return []
        try:
            with open(self.history_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
            
    def _save_history(self):
        try:
            self.history_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.history_path, "w", encoding="utf-8") as f:
                json.dump(self.history[-50:], f, indent=2) # Keep last 50 entries
        except Exception as e:
            print(f"[DuplicateDetector] Warning: Failed to save history: {e}")

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
    ) -> Tuple[bool, str, Dict]:
        """Evaluates whether the candidate video is a visual or structural duplicate.
        
        Args:
            video_path: Path to rendered MP4
            topic: Video topic
            title: YouTube title
            theme: 2D visual theme name (e.g. 'COSMIC', 'QUANTUM', 'SURVIVAL')
            palette: Active color palette name
            scene_sequence: List of scene archetypes used
            max_similarity_threshold: Maximum allowable perceptual similarity ratio
            
        Returns:
            (is_duplicate, reason_message, metadata)
        """
        # 1. Structural file integrity check
        valid, msg = self.validate_video_integrity(video_path)
        if not valid:
            return True, f"Quality Rejection: {msg}", {}

        # 2. Compute exact file SHA-256
        file_hash = compute_file_sha256(video_path)
        
        # 3. Check exact file duplicates
        for entry in self.history:
            if entry.get("file_hash") == file_hash:
                return True, f"Exact file duplicate detected (matches previously generated {entry.get('title')})", {}

        # 4. Extract perceptual frame hashes
        frame_hashes = extract_frame_dhashes(video_path)
        
        # 5. Check structural sequence against immediate predecessor
        if self.history:
            last_entry = self.history[-1]
            if (
                last_entry.get("theme") == theme and
                last_entry.get("palette") == palette and
                last_entry.get("scene_sequence") == scene_sequence
            ):
                return True, "Structural duplicate: Consecutive video cannot share identical theme, palette, and scene sequence.", {}

        # 6. Check perceptual similarity against the last 5 entries
        highest_similarity = 0.0
        most_similar_title = ""
        
        for entry in reversed(self.history[-5:]):
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

    def record_approved_video(self, metadata: Dict):
        """Records the newly approved video in the history ledger."""
        self.history.append(metadata)
        self._save_history()
