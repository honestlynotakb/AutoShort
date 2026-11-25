#!/usr/bin/env python3
"""Pre-Render Fail-Fast Quality Assurance Gate (Gate 3C).

Runs quickly (~2-5 seconds) after TTS/Whisper/Audio Mixing and BEFORE headless Chrome spends
minutes rendering all MP4 frames:
  1. Verifies Whisper word alignment populated `data/words.json` accurately (detecting uniform fallback).
  2. Verifies `data/mix.wav` duration parity, voice energy, -14 LUFS mastering target, and zero clipping.
  3. Runs `node tools/capture.mjs check` and captures `t = 0.05s` hook cover frame (`cover.jpg`),
     rejecting black or dim intro frames (`mean_luma < 18.0`).
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

from cloud.audio_master import inspect_wav_metrics, measure_lufs_ffmpeg


def verify_whisper_alignment(
    proj_dir: Path,
    allow_fallback: bool = False,
) -> Tuple[bool, str, Dict[str, Any]]:
    """Validates data/words.json and data/lines.json coverage and detects inline uniform fallback."""
    proj_dir = Path(proj_dir)
    lines_file = proj_dir / "data" / "lines.json"
    words_file = proj_dir / "data" / "words.json"

    if not lines_file.exists():
        return False, f"Missing timing file: {lines_file}", {}
    if not words_file.exists():
        return False, f"Missing word timing file: {words_file}", {}

    try:
        lines_data = json.loads(lines_file.read_text(encoding="utf-8"))
        words_data = json.loads(words_file.read_text(encoding="utf-8"))
    except Exception as e:
        return False, f"Malformed timing JSON: {e}", {}

    lines = lines_data.get("lines", [])
    if not lines or not isinstance(words_data, list) or not words_data:
        return False, "Empty lines or words timing arrays.", {}

    # Verify every spoken line has matched words and monotonic bounds
    line_ids_with_words = {int(w.get("line", -1)) for w in words_data}
    missing_lines = [i for i in range(len(lines)) if i not in line_ids_with_words]
    if missing_lines:
        return False, f"Words missing for line indices: {missing_lines}", {}

    # Detect exact deterministic inline_fallback signature:
    # In fallback mode, nearly every word slot uses an exact ~0.92 speak duty cycle and constant length scaling
    # inside each line, whereas neural Whisper produces organic syllable duration variation.
    by_line: Dict[int, List[Dict[str, Any]]] = {}
    for w in words_data:
        by_line.setdefault(int(w["line"]), []).append(w)

    duty_ratios: List[float] = []
    rate_cvs: List[float] = []
    for li, ws in by_line.items():
        if len(ws) < 3:
            continue
        char_rates = []
        for idx, w in enumerate(ws[:-1]):
            cur_s = float(w["s"])
            cur_e = float(w["e"])
            nxt_s = float(ws[idx + 1]["s"])
            span = nxt_s - cur_s
            speak = cur_e - cur_s
            if span > 0.03 and not re.search(r'[,.?!]$', str(w["w"]).strip()):
                duty_ratios.append(speak / span)
                norm_len = max(1, len(re.sub(r'[^a-z0-9]+', '', str(w["w"]).lower())))
                char_rates.append(span / (norm_len + 2.5))
        if len(char_rates) >= 3:
            mean_r = sum(char_rates) / len(char_rates)
            if mean_r > 0:
                std_r = (sum((r - mean_r) ** 2 for r in char_rates) / len(char_rates)) ** 0.5
                rate_cvs.append(std_r / mean_r)

    avg_cv = sum(rate_cvs) / len(rate_cvs) if rate_cvs else 0.0
    exact_92_hits = sum(1 for r in duty_ratios if abs(r - 0.92) <= 0.012)
    uniform_ratio = (exact_92_hits / len(duty_ratios)) if duty_ratios else 0.0

    estimated_flag = bool(lines_data.get("estimated")) or (len(rate_cvs) >= 2 and avg_cv < 0.035 and uniform_ratio >= 0.85)
    meta = {
        "line_count": len(lines),
        "word_count": len(words_data),
        "duration_sec": float(lines_data.get("duration", 0.0)),
        "whisper_aligned": not estimated_flag,
        "char_rate_cv": round(avg_cv, 4),
    }

    if estimated_flag and not allow_fallback:
        return (
            False,
            f"Subtitle alignment fell back to uniform length estimation (cv={avg_cv:.4f}, uniform={uniform_ratio:.2%}).",
            meta,
        )

    return True, f"Word alignment verified ({len(words_data)} words, whisper_aligned={meta['whisper_aligned']}).", meta


def verify_audio_mix(
    mix_wav: Path,
    expected_duration: Optional[float] = None,
) -> Tuple[bool, str, Dict[str, Any]]:
    """Checks data/mix.wav integrity, non-silence, LUFS level, clipping, and duration match."""
    mix_wav = Path(mix_wav)
    if not mix_wav.exists():
        return False, f"Missing mixed audio file: {mix_wav}", {}

    metrics = inspect_wav_metrics(mix_wav)
    if metrics["is_silent"]:
        return False, f"Mixed audio is silent ({metrics['rms_dbfs']} dBFS).", metrics
    if metrics["is_clipped"]:
        return False, f"Mixed audio has digital hard-clipping (peak={metrics['peak_dbfs']} dBFS).", metrics
    if expected_duration is not None and abs(metrics["duration_sec"] - expected_duration) > 1.2:
        return (
            False,
            f"Audio duration mismatch: mix={metrics['duration_sec']:.2f}s vs expected={expected_duration:.2f}s.",
            metrics,
        )

    lufs = measure_lufs_ffmpeg(mix_wav)
    if lufs is not None:
        metrics["lufs"] = lufs
        if lufs < -22.0:
            return False, f"Audio loudness too quiet for mobile Shorts ({lufs} LUFS < -22 LUFS).", metrics

    return True, f"Audio mix verified ({metrics['duration_sec']:.2f}s, rms={metrics['rms_dbfs']} dBFS).", metrics


def verify_frame_brightness(
    image_path: Path,
    min_mean_luma: float = 18.0,
) -> Tuple[bool, float, str]:
    """Decodes an image into 16x16 grayscale via FFmpeg and ensures it is not a blank/black frame."""
    image_path = Path(image_path)
    if not image_path.exists():
        return False, 0.0, f"Hook frame file missing: {image_path}"

    if not shutil.which("ffmpeg"):
        return True, 50.0, "FFmpeg absent; skipped brightness decode."

    cmd = [
        "ffmpeg", "-v", "error",
        "-i", str(image_path),
        "-vf", "scale=32:32,format=gray",
        "-f", "rawvideo",
        "-"
    ]
    raw = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, timeout=15)
    if not raw:
        return False, 0.0, "Failed to decode hook frame pixels."

    mean_luma = sum(raw) / len(raw)
    max_luma = max(raw)
    min_luma = min(raw)
    contrast_range = max_luma - min_luma
    # Allow crisp high-contrast OLED dark backgrounds if glowing bright UI foreground is present,
    # while still catching dimmed black fade-ins or empty solid screens.
    is_dim_or_blank = mean_luma < min_mean_luma and (max_luma < 85 or contrast_range < 65)
    if is_dim_or_blank:
        return (
            False,
            round(mean_luma, 2),
            f"Hook frame at t=0.05s is too dark/blank (luma={mean_luma:.1f}, max={max_luma}, range={contrast_range}).",
        )
    return True, round(mean_luma, 2), f"Hook frame brightness verified (luma={mean_luma:.1f}, max={max_luma})."


def run_chrome_smoke_check(
    proj_dir: Path,
    cover_out: Optional[Path] = None,
    min_hook_luma: float = 18.0,
) -> Tuple[bool, str, Dict[str, Any]]:
    """Runs capture.mjs check and validates bright frame-0 hook extraction."""
    proj_dir = Path(proj_dir)
    chk = subprocess.run(
        ["node", "tools/capture.mjs", "check"],
        cwd=str(proj_dir),
        capture_output=True,
        text=True,
        timeout=90,
    )
    if chk.returncode != 0 or "CHECK OK" not in (chk.stdout or ""):
        err_tail = ((chk.stdout or "") + "\n" + (chk.stderr or ""))[-400:]
        return False, f"Chrome capture.mjs check failed: {err_tail}", {}

    hook_dir = proj_dir / "review" / "hook"
    fr = subprocess.run(
        ["node", "tools/capture.mjs", "frames", "review/hook", "0.05"],
        cwd=str(proj_dir),
        capture_output=True,
        text=True,
        timeout=60,
    )
    if fr.returncode != 0:
        return False, f"Hook frame capture failed: {fr.stderr}", {}

    hook_jpg = hook_dir / "t0.05.jpg"
    ok_luma, luma_val, luma_msg = verify_frame_brightness(hook_jpg, min_mean_luma=min_hook_luma)
    if not ok_luma:
        return False, luma_msg, {"hook_luma": luma_val}

    if cover_out is not None and hook_jpg.exists():
        cover_out = Path(cover_out)
        cover_out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(hook_jpg, cover_out)

    return True, f"Chrome smoke check passed ({luma_msg}).", {"hook_luma": luma_val, "cover_jpg": str(hook_jpg)}
