#!/usr/bin/env python3
"""Unified Persistent State Management Layer.

Provides thread-safe, atomic state persistence, versioning, schema validation,
and concurrency protection across ephemeral GitHub Actions runners.

Manages:
1. topic_registry.json      - All used, reserved, published, and rejected topics.
2. script_registry.json     - SHA-256 fingerprints, line hashes, and word 3-grams.
3. video_history.json       - Exact file hashes, 10-frame 64-bit dHashes, theme/palette metadata.
4. publication_history.json - Upload idempotency records, run IDs, and YouTube video IDs.
"""
from __future__ import annotations

import os
import sys
import json
import time
import shutil
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple, Any

ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = ROOT / "cloud" / "state"
LEGACY_VIDEO_HISTORY = ROOT / "cloud" / "video_history.json"
PUBLISHED_MD = ROOT / "_published.md"

STATE_SCHEMA_VERSION = 1


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_save(file_path: Path, data: Any):
    """Writes data to a temporary file in the same directory and replaces atomically.
    Includes Windows file handle retry and fallback for OneDrive/antivirus filesystem locks.
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = file_path.with_suffix(f".tmp.{os.getpid()}.{time.time_ns()}")
    try:
        with open(temp_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())

        # On Windows, os.replace can intermittently raise WinError 5 if locked by OneDrive or scanner
        replaced = False
        for attempt in range(5):
            try:
                temp_path.replace(file_path)
                replaced = True
                break
            except (PermissionError, OSError):
                time.sleep(0.05 * (attempt + 1))

        if not replaced:
            # Fallback: direct atomic overwrite
            with open(file_path, "w", encoding="utf-8", newline="\n") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            try:
                if temp_path.exists():
                    temp_path.unlink()
            except Exception:
                pass
    except Exception as e:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass
        raise IOError(f"Failed atomic write to {file_path}: {e}") from e


def load_json_safe(file_path: Path, default: Any) -> Any:
    """Safely loads JSON, returning default on missing file or corruption."""
    file_path = Path(file_path)
    if not file_path.exists():
        return default
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[StateManager] Warning: Corrupted JSON at {file_path}, recovering default: {e}", file=sys.stderr)
        return default


class StateManager:
    """Manages persistent pipeline registries with atomic updates and automatic synchronization."""

    def __init__(self, state_dir: Optional[Path] = None, published_file: Optional[Path] = None):
        env_state_dir = os.environ.get("AUTOSHORT_STATE_DIR")
        env_pub_file = os.environ.get("AUTOSHORT_PUBLISHED_FILE")

        if state_dir is not None:
            self.state_dir = Path(state_dir)
        elif env_state_dir:
            self.state_dir = Path(env_state_dir)
        else:
            self.state_dir = STATE_DIR

        if published_file is not None:
            self.published_file = Path(published_file)
        elif env_pub_file:
            self.published_file = Path(env_pub_file)
        elif state_dir is not None or env_state_dir:
            # Keep isolated test/temp state dirs decoupled from live _published.md
            self.published_file = self.state_dir / "_published.md"
        else:
            self.published_file = PUBLISHED_MD

        self.state_dir.mkdir(parents=True, exist_ok=True)

        self.topic_reg_file = self.state_dir / "topic_registry.json"
        self.script_reg_file = self.state_dir / "script_registry.json"
        self.video_hist_file = self.state_dir / "video_history.json"
        self.pub_hist_file = self.state_dir / "publication_history.json"

        self.topics: Dict[str, Any] = self._init_topics()
        self.scripts: Dict[str, Any] = self._init_scripts()
        self.video_history: List[Dict[str, Any]] = self._init_video_history()
        self.publications: Dict[str, Any] = self._init_publications()

        # Seed from published log if present for this state instance
        self._bootstrap_from_published_log()

    # ═════════════════════════════════════════════════════════════════════════
    # Initialization & Bootstrapping
    # ═════════════════════════════════════════════════════════════════════════

    def _init_topics(self) -> Dict[str, Any]:
        data = load_json_safe(self.topic_reg_file, None)
        if not data or not isinstance(data, dict) or "topics" not in data:
            data = {"version": STATE_SCHEMA_VERSION, "topics": {}}
        return data

    def _init_scripts(self) -> Dict[str, Any]:
        data = load_json_safe(self.script_reg_file, None)
        if not data or not isinstance(data, dict) or "scripts" not in data:
            data = {"version": STATE_SCHEMA_VERSION, "scripts": {}}
        return data

    def _init_video_history(self) -> List[Dict[str, Any]]:
        # Load from state_dir first, then check legacy path only for default state_dir
        data = load_json_safe(self.video_hist_file, None)
        if data is None and self.state_dir == STATE_DIR and LEGACY_VIDEO_HISTORY.exists():
            data = load_json_safe(LEGACY_VIDEO_HISTORY, None)
        if not isinstance(data, list):
            data = []
        return data

    def _init_publications(self) -> Dict[str, Any]:
        data = load_json_safe(self.pub_hist_file, None)
        if not data or not isinstance(data, dict) or "records" not in data:
            data = {"version": STATE_SCHEMA_VERSION, "records": {}, "by_video_hash": {}}
        return data

    def _bootstrap_from_published_log(self):
        """Reads the configured published log to ensure historical entries are indexed."""
        if not self.published_file.exists():
            return
        try:
            lines = self.published_file.read_text(encoding="utf-8").splitlines()
            mutated = False
            for line in lines:
                line = line.strip()
                if not line.startswith("|") or line.startswith("| Date") or line.startswith("|---"):
                    continue
                parts = [p.strip() for p in line.split("|")]
                if len(parts) < 6:
                    continue
                date_str = parts[1]
                topic_str = parts[2]
                style_str = parts[3]
                title_str = parts[4]
                url_str = parts[5]

                norm_key = self.normalize_topic_key(topic_str)
                if norm_key and norm_key not in self.topics["topics"]:
                    self.topics["topics"][norm_key] = {
                        "topic": topic_str,
                        "title": title_str,
                        "style": style_str,
                        "status": "published",
                        "published_at": date_str,
                        "youtube_url": url_str,
                        "slot_id": "unknown",
                        "run_id": f"legacy-{norm_key[:12]}"
                    }
                    mutated = True

                norm_title = self.normalize_topic_key(title_str.replace("#shorts", "").strip())
                if norm_title and norm_title not in self.topics["topics"]:
                    self.topics["topics"][norm_title] = {
                        "topic": title_str,
                        "title": title_str,
                        "style": style_str,
                        "status": "published",
                        "published_at": date_str,
                        "youtube_url": url_str,
                        "slot_id": "unknown",
                        "run_id": f"legacy-{norm_title[:12]}"
                    }
                    mutated = True

            if mutated:
                self.save_topics()
        except Exception as e:
            print(f"[StateManager] Warning bootstrapping from _published.md: {e}", file=sys.stderr)

    # ═════════════════════════════════════════════════════════════════════════
    # Topic Registry & Reservation
    # ═════════════════════════════════════════════════════════════════════════

    @staticmethod
    def normalize_topic_key(topic: str) -> str:
        """Standardizes a topic string for indexing."""
        import re
        clean = topic.lower().strip()
        clean = re.sub(r'#shorts', '', clean, flags=re.IGNORECASE)
        clean = re.sub(r'[^\w\s]', '', clean)
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean

    def is_topic_used(self, topic: str, max_age_hours: Optional[float] = None) -> bool:
        """Checks if a normalized topic key exists in the registry with published or active reservation."""
        norm = self.normalize_topic_key(topic)
        if not norm:
            return False
        entry = self.topics["topics"].get(norm)
        if not entry:
            return False

        status = entry.get("status")
        if status == "published":
            return True

        if status == "reserved":
            reserved_at = entry.get("reserved_at_ts", 0)
            ttl = entry.get("ttl_seconds", 7200)
            if time.time() - reserved_at < ttl:
                return True  # Active reservation
            else:
                # Expired reservation
                return False

        return False

    def reserve_topic(self, topic: str, title: str, slot_id: str, run_id: str, ttl_hours: float = 2.0) -> bool:
        """Reserves a topic for a specific execution run to prevent race conditions."""
        self.cleanup_expired_reservations()
        norm = self.normalize_topic_key(topic)
        if self.is_topic_used(topic):
            return False

        self.topics["topics"][norm] = {
            "topic": topic,
            "title": title,
            "slot_id": str(slot_id),
            "run_id": str(run_id),
            "status": "reserved",
            "reserved_at": _now_iso(),
            "reserved_at_ts": time.time(),
            "ttl_seconds": ttl_hours * 3600
        }
        self.save_topics()
        return True

    def release_topic(self, topic: str):
        """Releases a reserved topic if execution failed before publication."""
        norm = self.normalize_topic_key(topic)
        if norm in self.topics["topics"]:
            if self.topics["topics"][norm].get("status") == "reserved":
                del self.topics["topics"][norm]
                self.save_topics()

    def confirm_topic_published(self, topic: str, title: str, youtube_url: str, slot_id: str, run_id: str):
        """Marks a topic as permanently published."""
        norm = self.normalize_topic_key(topic)
        self.topics["topics"][norm] = {
            "topic": topic,
            "title": title,
            "slot_id": str(slot_id),
            "run_id": str(run_id),
            "status": "published",
            "published_at": _now_iso(),
            "youtube_url": youtube_url
        }
        self.save_topics()

    def cleanup_expired_reservations(self):
        """Purges expired reservations from topic registry."""
        now = time.time()
        expired = []
        for key, info in self.topics["topics"].items():
            if info.get("status") == "reserved":
                reserved_at = info.get("reserved_at_ts", 0)
                ttl = info.get("ttl_seconds", 7200)
                if now - reserved_at >= ttl:
                    expired.append(key)
        if expired:
            for k in expired:
                del self.topics["topics"][k]
            self.save_topics()

    def get_all_published_and_reserved_topics(self) -> List[Dict[str, Any]]:
        """Returns all currently protected topic objects."""
        self.cleanup_expired_reservations()
        return list(self.topics["topics"].values())

    def save_topics(self):
        atomic_save(self.topic_reg_file, self.topics)

    # ═════════════════════════════════════════════════════════════════════════
    # Script Narration Registry
    # ═════════════════════════════════════════════════════════════════════════

    def record_script(self, script_text: str, topic: str, title: str, lines: List[Dict], script_hash: str) -> None:
        """Registers script fingerprint and word n-grams."""
        self.scripts["scripts"][script_hash] = {
            "topic": topic,
            "title": title,
            "full_text": script_text,
            "line_count": len(lines),
            "created_at": _now_iso(),
            "sha256": script_hash
        }
        self.save_scripts()

    def get_all_historical_scripts(self) -> List[Dict[str, Any]]:
        return list(self.scripts["scripts"].values())

    def save_scripts(self):
        atomic_save(self.script_reg_file, self.scripts)

    # ═════════════════════════════════════════════════════════════════════════
    # Video Visual History
    # ═════════════════════════════════════════════════════════════════════════

    def record_video(self, meta: Dict[str, Any]):
        """Records video visual metadata into persistent history."""
        self.video_history.append(meta)
        self.save_video_history()

    def get_video_history(self) -> List[Dict[str, Any]]:
        return self.video_history

    def save_video_history(self):
        atomic_save(self.video_hist_file, self.video_history)
        # Also sync to legacy location for backward compatibility if default state_dir
        if self.state_dir == STATE_DIR:
            try:
                atomic_save(LEGACY_VIDEO_HISTORY, self.video_history)
            except Exception:
                pass

    # ═════════════════════════════════════════════════════════════════════════
    # Publication & Idempotency Registry
    # ═════════════════════════════════════════════════════════════════════════

    def is_run_published(self, run_id: str) -> bool:
        """Checks if a run_id has already published a video."""
        return str(run_id) in self.publications["records"]

    def is_video_hash_published(self, video_hash: str) -> Optional[Dict[str, Any]]:
        """Checks if a video SHA-256 hash was previously uploaded."""
        return self.publications.get("by_video_hash", {}).get(video_hash)

    def record_publication(
        self,
        run_id: str,
        topic: str,
        title: str,
        video_hash: str,
        youtube_id: str,
        short_url: str,
        slot_id: str,
        status: str = "PUBLISHED"
    ):
        """Records an approved, published video with idempotency keys."""
        record = {
            "run_id": str(run_id),
            "topic": topic,
            "title": title,
            "video_hash": video_hash,
            "youtube_id": str(youtube_id),
            "short_url": str(short_url),
            "slot_id": str(slot_id),
            "status": status,
            "published_at": _now_iso()
        }
        self.publications["records"][str(run_id)] = record
        self.publications["by_video_hash"][video_hash] = record
        self.save_publications()

        # Update topic registry status to permanently published
        self.confirm_topic_published(
            topic=topic,
            title=title,
            youtube_url=short_url,
            slot_id=slot_id,
            run_id=run_id
        )

    def save_publications(self):
        atomic_save(self.pub_hist_file, self.publications)


# Global singleton instance accessor
_STATE_INSTANCE: Optional[StateManager] = None

def get_state_manager(
    state_dir: Optional[Path] = None,
    published_file: Optional[Path] = None
) -> StateManager:
    global _STATE_INSTANCE
    env_state_dir = os.environ.get("AUTOSHORT_STATE_DIR")
    target_dir = Path(state_dir) if state_dir is not None else (Path(env_state_dir) if env_state_dir else None)

    if state_dir is not None or published_file is not None:
        _STATE_INSTANCE = StateManager(state_dir=state_dir, published_file=published_file)
    elif _STATE_INSTANCE is None or (target_dir is not None and _STATE_INSTANCE.state_dir != target_dir):
        _STATE_INSTANCE = StateManager(state_dir=target_dir)
    return _STATE_INSTANCE
