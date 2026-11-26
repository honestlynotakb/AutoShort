# Potential Failures, Risks & Mitigation Register

This document catalogs all identified failure modes, edge-case risks, silent degradation vectors, and operational bottlenecks across the **Autonomous Daily YouTube Shorts** pipeline (`cloud/`, `faceless-shorts/`, and `.github/workflows/daily-shorts.yml`).

---

## 1. Repository & Asset Synchronization Risks

| ID | Severity | Component | Failure Mode | Root Cause / Trigger | Detection Signal | Mitigation & Test Coverage |
|---|---|---|---|---|---|---|
| **R-01** | **High** | `faceless-shorts/` vs `.agent/skills/faceless-shorts/` | **Split-brain skill copies** | `cloud_runner.py` and `visual_engine_2d.py` resolve `SKILL_DIR` to `faceless-shorts/` first, while `.agent/skills/faceless-shorts/` holds a separate copy. Edits to one copy silently miss the other. | Behavior differs between agent-invoked skill runs and CI `cloud_runner.py` runs. | Keep both `capture.mjs` copies synchronized; document single-source-of-truth convention. |
| **R-02** | **High** | `capture.mjs` | **120-second CI hang on JS parse errors** | Top-level ES module `SyntaxError` prevents `window.OP` from initializing; `openPage()` polled `window.OP` for 1200 iterations (120s) before timing out. | `boot timeout after 120s` followed by `EXCEPTION SyntaxError`. | Fail-fast check in `openPage()` aborts after ~1s when `document.readyState === 'complete'` and `Runtime.exceptionThrown` logged an `EXCEPTION `. |
| **R-03** | **High** | `cloud/style_router.py` | **Unquoted JS literals in Python f-strings** | Interpolating hex colors or strings inside `{...}` without JS quotes (e.g. `{'#DCE8F2' if is_snow ...}` -> `ctx.fillStyle = #DCE8F2;`) produces JS private-field `SyntaxError`. | `SyntaxError: Private field '#...' must be declared in an enclosing class`. | Always quote JS string literals or use `json.dumps()`; run `node --check` across all styles and topic variants (`test_stick_story_variants_valid_js_syntax`). |

---

## 2. Stage 0 & Curriculum / Gate 1–2 Failures

| ID | Severity | Component | Failure Mode | Root Cause / Trigger | Detection Signal | Mitigation & Test Coverage |
|---|---|---|---|---|---|---|
| **F-01** | **Medium** | `cloud/cloud_runner.py` (`generate_with_gemini`) | **Gemini API 429 / 5xx / timeout / retired model** | Upstream rate limits, transient 503s, or deprecated model IDs. | HTTP non-200 or `ModelNotFound` in logs; retries exhausted. | Multi-model fallback list + automatic failover to curated offline slots (`config/slots.json`). Tested in `test_cloud_runner.py`. |
| **F-02** | **Medium** | `cloud/cloud_runner.py` (`generate_with_gemini`) | **Malformed or markdown-wrapped JSON from LLM** | Gemini returns prose around JSON, invalid JSON, or missing `topic`/`title`/`lines` keys. | `json.JSONDecodeError` or schema validation failure. | Strip markdown fences, validate required fields, feed rejection constraints back into retry prompt, and fall back safely. |
| **F-03** | **High** | `cloud/cloud_runner.py` (`pick_topic_for_slot`) | **Curriculum exhaustion** | All 30+ fallback topics in all 3 slots are marked published and Gemini is unavailable. | `RuntimeError` raised before scaffolding. | Runway warning logged when remaining fallbacks <= 5 (`compute_curriculum_runway`); safe `RuntimeError` prevents duplicate uploads. |
| **F-04** | **Medium** | `cloud/topic_guard.py` & `state_manager.py` | **Topic reservation leak on crash** | `reserve_if_unique` marks a topic `reserved`; an unhandled exception before `release_topic` leaves it locked. | Subsequent runs skip the topic indefinitely. | Explicit `state_mgr.release_topic(topic)` on Gate 3, 3C, and 4 rejections; `try/finally` recommended for unexpected crashes. |
| **F-05** | **Medium** | `cloud/cloud_runner.py` (`sanitize_text_for_tts`) | **Kokoro ONNX crash on Unicode / emojis** | Smart quotes, em-dashes, or emoji characters in LLM output cause phonemizer/TTS errors. | Non-zero exit in Stage 1 `voice.py`. | `sanitize_text_for_tts()` normalizes punctuation and strips unsupported Unicode prior to `script.json` creation. |

---

## 3. Stage 0.5 Visual Scaffolding & Gate 3 / 3B Failures

| ID | Severity | Component | Failure Mode | Root Cause / Trigger | Detection Signal | Mitigation & Test Coverage |
|---|---|---|---|---|---|---|
| **F-06** | **Medium** | `cloud/cloud_runner.py` + `asset_guard.py` | **Gate 3/3B 5-attempt exhaustion** | Recent history blocks all 5 `variant` attempts due to palette/card/theme collisions. | `ValueError: Gate 3 Asset/Visual Uniqueness Rejected after 5 attempts`. | `variant_offset` rotates styles (`select_visual_style`) and palettes (`pick_variation_palette`). |
| **F-07** | **Medium** | `cloud/visual_engine_2d.py` | **Generated `tools/mix.py` syntax or runtime error** | Invalid `music_config` values (e.g. `bpm <= 0`, `root_hz <= 0`, missing mood key). | `mix.py` fails in Stage 3 with `ZeroDivisionError` or `SyntaxError`. | `ast.parse()` / `py_compile` validation in `test_visual_and_style.py`; safe defaults in `build_music_config()`. |
| **F-08** | **Low** | `cloud/visual_engine_2d.py` & `style_router.py` | **Caption zone overlap (`y=1250..1550`)** | Cards/widgets placed in the lower-third caption safe zone obscure word-synced captions. | Visual overlap in rendered MP4. | `test_gate3_caption_safe_zone_no_overlap` asserts widgets stay above caption band. |

---

## 4. Stage 1–3.5 TTS, Whisper, Audio Mastering & Gate 3C Failures

| ID | Severity | Component | Failure Mode | Root Cause / Trigger | Detection Signal | Mitigation & Test Coverage |
|---|---|---|---|---|---|---|
| **F-09** | **High** | `faceless-shorts/scripts/words.py` + `preflight_qa.py` | **Silent Whisper fallback to uniform word timing** | `faster-whisper` fails or is skipped, writing uniform `0.92` duty-cycle estimates to `words.json`. | Desynchronized captions in rendered video. | `verify_whisper_alignment()` detects low `char_rate_cv` + `0.92` duty-cycle signature and rejects when `REQUIRE_WHISPER=1`. |
| **F-10** | **High** | `cloud/audio_master.py` | **Silent or hard-clipped `data/mix.wav`** | `mix.py` writes zeroed samples or gain staging clips above `0 dBFS`. | `is_silent` (`rms_dbfs < -40`) or `is_clipped` in `inspect_wav_metrics()`. | Gate 3C `verify_audio_mix()` aborts before expensive Chrome rendering. |
| **F-11** | **Medium** | `cloud/audio_master.py` | **FFmpeg `loudnorm` JSON parse failure** | FFmpeg missing, timeout (>30s), or stderr lacks `input_i` JSON block. | `measure_lufs_ffmpeg()` returns `None`; mastering skipped (`applied=False`). | Graceful fallback preserves original WAV; `verify_audio_mix()` still enforces RMS/peak/duration checks. |
| **F-12** | **High** | `cloud/preflight_qa.py` (`run_chrome_smoke_check`) | **Black or dim frame-0 hook (`t=0.05s`)** | Fade-in from black in `main.js` or broken canvas draw leaves `mean_luma < 18.0`. | Shorts feed thumbnail appears black. | `verify_frame_brightness()` decodes `t0.05.jpg` via FFmpeg and rejects dim/blank frames. |

---

## 5. Stage 4–4.5 Chrome Rendering & Gate 4 Failures

| ID | Severity | Component | Failure Mode | Root Cause / Trigger | Detection Signal | Mitigation & Test Coverage |
|---|---|---|---|---|---|---|
| **F-13** | **High** | `capture.mjs` (`video` mode) | **Headless Chrome / SwiftShader OOM or timeout** | High resolution/FPS or WebGL memory leak on GitHub Actions `ubuntu-latest` (7 GB RAM). | Chrome process killed (`SIGKILL`) or 60-min workflow timeout. | Workflow enforces `FPS=24`, `QS=&res=0.55&aa=1&shadow=512`, `SOFTWARE_GL=1`, and `--disable-dev-shm-usage`. |
| **F-14** | **Medium** | `cloud/duplicate_detector.py` | **Corrupted `video_history.json` or blank video frames** | Truncated JSON write or all-black render output. | `json.JSONDecodeError` or `is_blank_or_solid_frame()` returns `True`. | `load_json_safe` recovers `[]`; `validate_video_integrity()` rejects 0-byte, <3s, or >65s videos. |

---

## 6. Stage 5 Publishing, State Persistence & GitHub Actions Failures

| ID | Severity | Component | Failure Mode | Root Cause / Trigger | Detection Signal | Mitigation & Test Coverage |
|---|---|---|---|---|---|---|
| **F-15** | **High** | `cloud/upload_youtube.py` | **YouTube Data API `quotaExceeded` (403) or `invalid_grant`** | >10,000 daily quota units (1,600/upload) or revoked/expired OAuth refresh token. | `HttpError` 403 or `invalid_grant` in Stage 5. | Explicit error logging; Gate 5 idempotency prevents double-upload retries on `run_id` or `video_hash`. |
| **F-16** | **Medium** | `cloud/upload_helper.py` | **Direct mirror host outage (`uguu.se` / `catbox.moe`)** | Temporary 5xx, rate limit, or HEAD-request rejection on mirror host. | `RuntimeError: All direct video hosting endpoints failed.` | 3 retries on `uguu.se`, automatic failover to `catbox.moe`, Range GET fallback in `verify_direct_url()`. |
| **F-17** | **Medium** | `.github/workflows/daily-shorts.yml` | **Concurrent `git push` conflict** | Two scheduled/manual runs finish near-simultaneously and push to `main`. | `git push` rejected (non-fast-forward). | Workflow runs `git pull --rebase --autostash origin main` with 3 retry attempts; `concurrency` group serializes non-push runs. |
| **F-18** | **Low** | `cloud/state_manager.py` (`atomic_save`) | **Windows OneDrive / AV file lock (`WinError 5`)** | `Path.replace()` fails transiently while OneDrive indexes `.json` state files. | `PermissionError` during `atomic_save`. | 5-attempt exponential sleep retry + direct overwrite fallback + temp file cleanup. |
