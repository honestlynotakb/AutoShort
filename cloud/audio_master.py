#!/usr/bin/env python3
"""Shorts Audio Mastering & Loudness Verification Engine (-14 LUFS Target).

Provides:
1. Pure-stdlib PCM WAV inspection (`inspect_wav_metrics`) for RMS, peak, duration, silence/clip checks.
2. Integrated loudness measurement (`measure_lufs_ffmpeg`) via FFmpeg `loudnorm`.
3. Non-destructive in-place mastering (`normalize_to_lufs_ffmpeg`) applying warm voice presence EQ,
   gentle dynamic glue, and EBU R128 -14.0 LUFS / -1.0 dBTP limiting suitable for YouTube Shorts.
"""
from __future__ import annotations

import os
import re
import wave
import json
import math
import array
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional


def inspect_wav_metrics(wav_path: Path) -> Dict[str, Any]:
    """Reads a PCM WAV file using stdlib wave/array and returns duration, RMS dBFS, and peak dBFS."""
    wav_path = Path(wav_path)
    if not wav_path.exists():
        raise FileNotFoundError(f"WAV file not found: {wav_path}")

    with wave.open(str(wav_path), "rb") as wf:
        channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        nframes = wf.getnframes()
        raw = wf.readframes(nframes)

    duration_sec = round(nframes / float(framerate), 3) if framerate > 0 else 0.0
    if nframes == 0 or not raw:
        return {
            "duration_sec": 0.0,
            "sample_rate": framerate,
            "channels": channels,
            "rms_dbfs": -96.0,
            "peak_dbfs": -96.0,
            "max_abs_sample": 0,
            "is_silent": True,
            "is_clipped": False,
        }

    if sampwidth == 2:
        samples = array.array("h")
        samples.frombytes(raw)
        max_scale = 32768.0
    elif sampwidth == 4:
        samples = array.array("i")
        samples.frombytes(raw)
        max_scale = 2147483648.0
    else:
        # Generic byte fallback for 8-bit unsigned WAV
        u8 = array.array("B", raw)
        max_abs = max((abs(b - 128) for b in u8), default=0)
        mean_sq = sum(((b - 128) / 128.0) ** 2 for b in u8) / max(1, len(u8))
        rms = math.sqrt(mean_sq)
        rms_db = round(20.0 * math.log10(max(rms, 1e-6)), 2)
        peak_db = round(20.0 * math.log10(max(max_abs / 128.0, 1e-6)), 2)
        return {
            "duration_sec": duration_sec,
            "sample_rate": framerate,
            "channels": channels,
            "rms_dbfs": rms_db,
            "peak_dbfs": peak_db,
            "max_abs_sample": max_abs,
            "is_silent": rms_db < -40.0,
            "is_clipped": max_abs >= 127,
        }

    total_samples = len(samples)
    step = max(1, total_samples // 150000)  # Fast bounded subsampling for long mixes
    sum_sq = 0.0
    count = 0
    max_abs = 0
    for idx in range(0, total_samples, step):
        val = samples[idx]
        aval = -val if val < 0 else val
        if aval > max_abs:
            max_abs = aval
        norm = aval / max_scale
        sum_sq += norm * norm
        count += 1

    # Also check exact peak across all samples
    full_max = max(abs(min(samples)), abs(max(samples))) if samples else 0
    if full_max > max_abs:
        max_abs = full_max

    rms = math.sqrt(sum_sq / max(1, count))
    peak = max_abs / max_scale
    rms_dbfs = round(20.0 * math.log10(max(rms, 1e-6)), 2)
    peak_dbfs = round(20.0 * math.log10(max(peak, 1e-6)), 2)

    return {
        "duration_sec": duration_sec,
        "sample_rate": framerate,
        "channels": channels,
        "rms_dbfs": rms_dbfs,
        "peak_dbfs": peak_dbfs,
        "max_abs_sample": int(max_abs),
        "is_silent": rms_dbfs < -40.0,
        "is_clipped": max_abs >= int(max_scale) - 1,
    }


def _parse_loudnorm_json(stderr_text: str) -> Optional[Dict[str, Any]]:
    matches = re.findall(r'\{[^{}]*"input_i"[^{}]*\}', stderr_text, re.DOTALL)
    if not matches:
        return None
    try:
        return json.loads(matches[-1])
    except Exception:
        return None


def measure_lufs_ffmpeg(wav_path: Path, target_lufs: float = -14.0, true_peak: float = -1.0) -> Optional[float]:
    """Measures integrated LUFS of an audio file via FFmpeg loudnorm dry pass."""
    wav_path = Path(wav_path)
    if not wav_path.exists() or not shutil.which("ffmpeg"):
        return None

    cmd = [
        "ffmpeg", "-hide_banner", "-y",
        "-i", str(wav_path),
        "-af", f"loudnorm=I={target_lufs}:TP={true_peak}:LRA=9:print_format=json",
        "-f", "null", "-"
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        parsed = _parse_loudnorm_json(proc.stderr or "")
        if parsed and "input_i" in parsed:
            val = float(parsed["input_i"])
            if math.isfinite(val):
                return round(val, 2)
    except Exception:
        pass
    return None


def normalize_to_lufs_ffmpeg(
    wav_path: Path,
    target_lufs: float = -14.0,
    true_peak: float = -1.0,
    apply_voice_polish: bool = True,
) -> Dict[str, Any]:
    """Applies calm vocal presence polish and -14 LUFS mastering in-place using atomic replace."""
    wav_path = Path(wav_path)
    before = inspect_wav_metrics(wav_path)
    if before["is_silent"]:
        raise ValueError(f"Cannot master silent audio track ({before['rms_dbfs']} dBFS): {wav_path}")

    if not shutil.which("ffmpeg"):
        return {
            "applied": False,
            "reason": "ffmpeg binary unavailable",
            "before_metrics": before,
            "after_metrics": before,
            "target_lufs": target_lufs,
        }

    filter_parts = []
    if apply_voice_polish:
        # Clean sub-bass rumble (<85Hz), subtle 3.2kHz presence boost for clarity, gentle glue compression
        filter_parts.extend([
            "highpass=f=85",
            "equalizer=f=3200:t=q:w=1.2:g=2.0",
            "acompressor=threshold=-20dB:ratio=2.4:attack=8:release=120",
        ])
    filter_parts.append(f"loudnorm=I={target_lufs:.1f}:TP={true_peak:.1f}:LRA=9")
    af_chain = ",".join(filter_parts)

    tmp_out = wav_path.with_suffix(".master.tmp.wav")
    try:
        cmd = [
            "ffmpeg", "-v", "error", "-y",
            "-i", str(wav_path),
            "-af", af_chain,
            "-ar", "48000",
            "-ac", "2",
            "-c:a", "pcm_s16le",
            str(tmp_out),
        ]
        subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=60)
        after = inspect_wav_metrics(tmp_out)
        if after["is_silent"] or after["duration_sec"] <= 0.5:
            raise RuntimeError(f"Mastered WAV invalid: {after}")
        os.replace(tmp_out, wav_path)
        measured_lufs = measure_lufs_ffmpeg(wav_path, target_lufs=target_lufs, true_peak=true_peak)
        after["lufs"] = measured_lufs
        return {
            "applied": True,
            "before_metrics": before,
            "after_metrics": after,
            "target_lufs": target_lufs,
        }
    except Exception:
        if tmp_out.exists():
            try:
                tmp_out.unlink()
            except OSError:
                pass
        raise
