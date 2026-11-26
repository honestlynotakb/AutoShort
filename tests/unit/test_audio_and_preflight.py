"""Unit tests for cloud.audio_master and cloud.preflight_qa."""
import json
import math
import shutil
import struct
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import MagicMock, patch

from cloud.audio_master import (
    _parse_loudnorm_json,
    inspect_wav_metrics,
    measure_lufs_ffmpeg,
    normalize_to_lufs_ffmpeg,
)
from cloud.preflight_qa import (
    run_chrome_smoke_check,
    verify_audio_mix,
    verify_frame_brightness,
    verify_whisper_alignment,
)


def _write_pcm_wav(path: Path, samples, sr: int = 48000, sampwidth: int = 2, channels: int = 1):
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(sr)
        if sampwidth == 1:
            wf.writeframes(bytes(samples))
        elif sampwidth == 2:
            wf.writeframes(struct.pack(f"<{len(samples)}h", *samples))
        elif sampwidth == 4:
            wf.writeframes(struct.pack(f"<{len(samples)}i", *samples))


class TestAudioAndPreflightUnit(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="unit_audio_"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_inspect_wav_metrics_8_16_32_bit_empty_and_clipped(self):
        with self.assertRaises(FileNotFoundError):
            inspect_wav_metrics(self.tmp / "missing.wav")

        empty_wav = self.tmp / "empty.wav"
        _write_pcm_wav(empty_wav, [], sampwidth=2)
        self.assertTrue(inspect_wav_metrics(empty_wav)["is_silent"])

        u8_wav = self.tmp / "u8.wav"
        _write_pcm_wav(u8_wav, [128, 200, 50, 128] * 100, sampwidth=1)
        m8 = inspect_wav_metrics(u8_wav)
        self.assertFalse(m8["is_silent"])

        s32_wav = self.tmp / "s32.wav"
        _write_pcm_wav(s32_wav, [0, 500_000_000, -500_000_000] * 100, sampwidth=4)
        m32 = inspect_wav_metrics(s32_wav)
        self.assertFalse(m32["is_silent"])

        clipped_wav = self.tmp / "clipped.wav"
        _write_pcm_wav(clipped_wav, [32767, -32768] * 200, sampwidth=2)
        self.assertTrue(inspect_wav_metrics(clipped_wav)["is_clipped"])

    def test_parse_loudnorm_json_and_measure_lufs(self):
        stderr = 'noise\n{\n  "input_i": "-14.20",\n  "input_tp": "-1.10"\n}\n'
        parsed = _parse_loudnorm_json(stderr)
        self.assertEqual(parsed["input_i"], "-14.20")
        self.assertIsNone(_parse_loudnorm_json("no json here"))

        wav = self.tmp / "tone.wav"
        tone = [int(4000 * math.sin(2 * math.pi * 440 * i / 48000)) for i in range(4800)]
        _write_pcm_wav(wav, tone)

        mock_proc = MagicMock(stderr=stderr, returncode=0)
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            with patch("subprocess.run", return_value=mock_proc):
                self.assertEqual(measure_lufs_ffmpeg(wav), -14.2)

    def test_normalize_to_lufs_skips_when_ffmpeg_missing(self):
        wav = self.tmp / "tone.wav"
        tone = [int(4000 * math.sin(2 * math.pi * 440 * i / 48000)) for i in range(4800)]
        _write_pcm_wav(wav, tone)
        with patch("shutil.which", return_value=None):
            res = normalize_to_lufs_ffmpeg(wav)
        self.assertFalse(res["applied"])

    def test_verify_whisper_alignment_detects_uniform_fallback_and_passes_organic(self):
        pdir = self.tmp / "align"
        (pdir / "data").mkdir(parents=True)
        (pdir / "data" / "lines.json").write_text(
            json.dumps({"duration": 4.0, "lines": [{"text": "a b c d"}, {"text": "e f g h"}]}),
            encoding="utf-8",
        )
        # Uniform 0.92 duty cycle & constant length scaling -> flagged
        words_uniform = []
        t = 0.0
        for li in (0, 1):
            for w in ("alpha", "bravo", "charlie", "delta"):
                span = 0.05 * (len(w) + 2.5)
                words_uniform.append({"line": li, "w": w, "s": round(t, 4), "e": round(t + span * 0.92, 4)})
                t += span
        (pdir / "data" / "words.json").write_text(json.dumps(words_uniform), encoding="utf-8")
        ok, _, meta = verify_whisper_alignment(pdir, allow_fallback=False)
        self.assertFalse(ok)
        self.assertFalse(meta["whisper_aligned"])

        ok_allow, _, _ = verify_whisper_alignment(pdir, allow_fallback=True)
        self.assertTrue(ok_allow)

    def test_verify_audio_mix_and_frame_brightness_and_chrome_smoke(self):
        wav = self.tmp / "mix.wav"
        tone = [int(4000 * math.sin(2 * math.pi * 440 * i / 48000)) for i in range(48000)]
        _write_pcm_wav(wav, tone)
        with patch("cloud.preflight_qa.measure_lufs_ffmpeg", return_value=-14.0):
            ok, _, _ = verify_audio_mix(wav, expected_duration=1.0)
            self.assertTrue(ok)
            ok_dur, _, _ = verify_audio_mix(wav, expected_duration=5.0)
            self.assertFalse(ok_dur)

        with patch("cloud.preflight_qa.measure_lufs_ffmpeg", return_value=-28.0):
            ok_quiet, _, _ = verify_audio_mix(wav, expected_duration=1.0)
            self.assertFalse(ok_quiet)

        img = self.tmp / "hook.jpg"
        img.write_bytes(b"fakejpg")
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            with patch("subprocess.check_output", return_value=bytes([5] * 1024)):
                ok_dark, _, _ = verify_frame_brightness(img)
                self.assertFalse(ok_dark)
            with patch("subprocess.check_output", return_value=bytes([120] * 1024)):
                ok_bright, _, _ = verify_frame_brightness(img)
                self.assertTrue(ok_bright)

        proj = self.tmp / "smoke_proj"
        (proj / "review" / "hook").mkdir(parents=True)
        (proj / "review" / "hook" / "t0.05.jpg").write_bytes(b"fakejpg")
        with patch("subprocess.run", side_effect=[MagicMock(returncode=0, stdout="CHECK OK"), MagicMock(returncode=0)]):
            with patch("cloud.preflight_qa.verify_frame_brightness", return_value=(True, 110.0, "ok")):
                ok_ch, _, _ = run_chrome_smoke_check(proj, cover_out=proj / "renders" / "cover.jpg")
                self.assertTrue(ok_ch)
                self.assertTrue((proj / "renders" / "cover.jpg").exists())


if __name__ == "__main__":
    unittest.main()
