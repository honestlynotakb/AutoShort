# Error Audit Log & Retrospective: Autonomous YouTube Shorts Engine

**System:** Autonomous 5-Times-Daily YouTube Shorts Pipeline  
**Target Channel:** Ayaan Kashif (`UCHNvsA_nL4uSyZIr8RX9Zyw`)  
**Repository:** `honestlynotakb/AutoShort` (`main` branch)  
**Lead Architecture:** Automated Serverless Cloud Pipeline (GitHub Actions + Google Generative AI + Kokoro ONNX + Faster-Whisper + Headless Chrome Three.js + YouTube Data API v3)  
**Last Updated:** 2026-11-11  

---

## 1. Executive Summary & Incident History

This document serves as the permanent post-mortem registry and living reliability audit for the autonomous video generation and publication system. Over the initial development and cloud deployment lifecycle, the system encountered several failure modes spanning operating system socket semantics, cloud sandbox memory boundaries, browser module resolution, and API authentication models.

Every incident has been investigated to root cause, patched with permanent architectural guardrails, and integrated into our continuous verification test suite.

```
       [Incident ERR-003]            [Incident ERR-005]            [Incident ERR-007]
       OS Socket Collision           Subtitle Timing Crash         Three.js Import Timeout
             │                             │                             │
┌────────────▼─────────────────────────────▼─────────────────────────────▼──────────────────┐
│                             PRODUCTION INCIDENT TIMELINE                                  │
└────────────┬─────────────────────────────┬─────────────────────────────┬──────────────────┘
             │                             │                             │
       [Incident ERR-004]            [Incident ERR-006]            [Incident ERR-008]
       GCP OAuth 403 Sandbox         Chrome /dev/shm Freeze        Gemini API 404 / Multi-Model
```

---

## 2. Comprehensive Incident Post-Mortem Registry

### Incident ERR-001: Path Resolution Failure in Local Helper Execution
- **Date & Environment:** Local Windows Workstation (PowerShell)
- **Symptom:** Terminal threw `C:\Users\DELL\cloud\get_youtube_token.py: No such file or directory`.
- **Root Cause:** Script was invoked using a relative path from the user profile directory rather than from within the active project workspace (`C:\Users\DELL\OneDrive\Desktop\Shorts auto\`).
- **Immediate Patch:** Specified fully qualified absolute path in execution instructions.
- **Architectural Mitigation:** Updated all cloud and local helper scripts to dynamically resolve project roots using `Path(__file__).resolve().parent.parent` rather than depending on `os.getcwd()` or shell working directory state.

---

### Incident ERR-002: Virtual Environment Toolchain Incompleteness (`pip` missing)
- **Date & Environment:** Local Python Virtual Environment (`.venv`)
- **Symptom:** Command `python -m pip install google-auth-oauthlib` returned `No module named pip`.
- **Root Cause:** A bare or minimal Python virtual environment had been initialized without the `ensurepip` bootstrapping module.
- **Immediate Patch:** Utilized `uv pip install --python ... google-auth-oauthlib` to leverage fast external wheel installation.
- **Architectural Mitigation:** Hardened `.github/workflows/daily-shorts.yml` to explicitly invoke `python -m pip install --upgrade pip` and install from `cloud/requirements.txt` to eliminate host environment discrepancy.

---

### Incident ERR-003: Port Address Conflict on Static OAuth Loopback (`WinError 10048`)
- **Date & Environment:** Local Windows Workstation (`run_auth.py`)
- **Symptom:** `OSError: [WinError 10048] Only one usage of each socket address (protocol/network address/port) is normally permitted`.
- **Root Cause:** `InstalledAppFlow.run_local_server(port=8080)` hardcoded static TCP port 8080. A lingering background service or previous zombie Python process held an active socket on port 8080.
- **Immediate Patch:** Terminated orphan listener processes.
- **Architectural Mitigation:** Refactored `cloud/get_youtube_token.py` and `cloud/run_auth.py` to use dynamic OS port allocation (`port=0`). When binding to port 0, the operating system assigns an available ephemeral TCP port automatically, preventing port collisions.

---

### Incident ERR-004: Google Cloud OAuth 403 `access_denied` / App Not Verified
- **Date & Environment:** Google Cloud Console / OAuth 2.0 Consent Screen
- **Symptom:** Browser authentication redirected to Google warning screen with error `403: access_denied - AutoShort has not completed the Google verification process`.
- **Root Cause:** The Google Cloud OAuth 2.0 Consent Screen was published in "External / Testing" mode. In this mode, Google's identity servers strictly reject any Google account not explicitly registered in the project's authorized "Test Users" whitelist.
- **Immediate Patch:** Added `ayaankashifbutt1@gmail.com` to the "Test users" list in Google Cloud Console.
- **Architectural Mitigation:** Documented the OAuth setup procedure in `docs/` and validated that the resulting `refresh_token` has offline persistence, removing the need for interactive re-authentication during headless cloud execution.

---

### Incident ERR-005: Static Subtitle Keyword Lookup Crash in Dynamic Scripts
- **Date & Environment:** GitHub Actions Run #1 (Ubuntu Runner)
- **Symptom:** Pipeline failed at audio cue capture: `boot failed: ERR:Error: word "blood" not found in line 2`.
- **Root Cause:** The upstream template's `timing.js` file contained hardcoded keyword searches (e.g. searching for the word `"blood"` in line 2) designed for a static template demo. When dynamic AI-generated scripts were supplied, the keyword was absent, causing an unhandled exception inside headless Chrome.
- **Immediate Patch:** Updated `timing.js` to catch keyword lookups and safely fall back to the line's natural midpoint timestamp `(line.s + line.e) / 2`.
- **Architectural Mitigation:** Refactored `cloud_runner.py::write_adaptive_shots()` to generate deterministic cut timestamps using `cut(i) = L(i) - 0.08`, completely decoupling visual camera transitions from fragile word-level lexical searches.

---

### Incident ERR-006: Headless Chrome Hang & Resource Starvation (Ubuntu 64MB `/dev/shm`)
- **Date & Environment:** GitHub Actions Run #2 (Ubuntu Runner)
- **Symptom:** Workflow ran for 21 minutes and 11 seconds without making progress, eventually triggering a runner cancellation.
- **Root Cause:** Standard Linux container environments allocate only 64MB of shared memory (`/dev/shm`). When headless Chrome renders high-resolution frames (1080x1920 @ 30 FPS) with WebGL / SwiftShader, memory buffers quickly overflow the 64MB limit, causing the Chrome renderer process to deadlock silently.
- **Immediate Patch:** Added `--no-sandbox`, `--disable-dev-shm-usage`, and `--disable-gpu-sandbox` flags to all `capture.mjs` invocations.
- **Architectural Mitigation:** Passing `--disable-dev-shm-usage` forces Chrome to allocate rendering memory in `/tmp` rather than `/dev/shm`, providing unrestricted buffer space and preventing container freezes.

---

### Incident ERR-007: Three.js Module Resolution Failure & Boot Timeout (`TypeError`)
- **Date & Environment:** GitHub Actions Run #3 (Ubuntu Runner)
- **Symptom:** Headless browser failed during cue generation:
  ```
  Error: boot timeout
  TypeError: Failed to resolve module specifier "three". Relative references must start with either "/", "./", or "../".
  ```
- **Root Cause:** Slot 1 ("Geography & Flag Knowledge") was designated with `"style": "paper-atlas"`. `paper-atlas` is a lightweight 2D Canvas engine that lacks Three.js vendor dependencies and has no `<script type="importmap">` in its `index.html`. However, `cloud_runner.py`'s adaptive camera shot generator automatically injected Three.js imports (`import * as THREE from 'three';`). Headless Chrome could not resolve `"three"` and threw a fatal unhandled `TypeError`, preventing `window.OP.ready` from ever signaling true.
- **Immediate Patch:** Updated `config/slots.json` to configure Slot 1 as `"style": "deep-dive"`.
- **Architectural Mitigation:** Standardized all 5 slots and locked `cloud_runner.py` project scaffolding exclusively to the `deep-dive` 3D engine (`SKILL_DIR / 'styles' / 'deep-dive' / 'example'`). This guarantees that every generated short has the Three.js import map and local vendor bundle (`vendor/three.module.js`) pre-wired.

---

### Incident ERR-008: Gemini API Model URI Mismatches & Authentication Header Rejections
- **Date & Environment:** GitHub Actions Runs #1–#3
- **Symptom:** Cloud logs indicated:
  ```
  HTTP Error 404: Not Found
  Gemini API generation failed ... falling back to slot curriculum...
  ```
- **Root Cause:** The REST endpoint for Google Generative AI has subtle behavioral differences across API versions (`v1` vs `v1beta`) and model identifiers (e.g. `gemini-1.5-flash` vs `gemini-2.0-flash`). Additionally, passing keys strictly via headers vs query parameters (`?key=...`) can result in 404/401 errors depending on regional Google Cloud endpoints.
- **Immediate Patch:** The pipeline gracefully activated its deterministic offline curriculum fallback, producing a high-quality video without halting.
- **Architectural Mitigation:** Re-engineered `cloud_runner.py::generate_with_gemini()` to use a cascading model pool (`gemini-2.0-flash`, `gemini-1.5-flash`, `gemini-2.5-flash`) iterating across both `v1beta` and `v1` and supplying credentials simultaneously via HTTP headers and the `?key=` query parameter.

---

### Incident ERR-009: YAML Parser Mapping Conflict on Unquoted `run-name`
- **Date & Environment:** GitHub Actions Workflow Configuration
- **Symptom:** `yaml.scanner.ScannerError: mapping values are not allowed here` on workflow line parsing.
- **Root Cause:** An unquoted GitHub Actions expression containing colons (`'Short: {0}'`) and curly brackets inside an interpolated block was interpreted by YAML parsers as an illegal dictionary mapping key.
- **Immediate Patch:** Enclosed the `run-name` expression in standard double quotes (`"${{ ... }}"`).
- **Architectural Mitigation:** Quoted top-level `'on':` triggers and interpolated workflow directives, preventing YAML 1.1 boolean coercion and mapping ambiguity.

---

### Incident ERR-010: Git Rebase Push Collisions on Shallow Clones & CRLF/LF Churn
- **Date & Environment:** GitHub Actions CI Runner Git Push Step
- **Symptom:** Publication log commits failed on concurrent runs with `[rejected] (fetch first)` or shallow rebase refusal.
- **Root Cause:** Default `actions/checkout@v4` uses `fetch-depth: 1` (shallow history). In a shallow checkout, rebasing fails with `refusing to merge unrelated histories`. Additionally, missing `.gitattributes` caused line-ending divergence between Windows CRLF and Linux LF.
- **Immediate Patch:** Added `.gitattributes` enforcing universal `eol=lf`, normalized `_published.md`, and configured `fetch-depth: 0`.
- **Architectural Mitigation:** Engineered a 3-attempt automated rebase loop (`git fetch origin main` + `git rebase origin/main` + `git push origin main`) to guarantee zero-downtime log persistence.

---

### Incident ERR-011: SwiftShader CPU Software Rendering Timeout on 30-Minute Job Ceiling
- **Date & Environment:** GitHub Actions Scheduled Execution (`make-and-publish-short`, Run #43202273942)
- **Symptom:** Workflow ran for 29 minutes and 15 seconds during `python cloud/cloud_runner.py --slot "auto"`, then abruptly failed with `Error: The operation was canceled.` after exactly 30 minutes 17 seconds.
- **Root Cause:** In standard 2-vCPU Ubuntu GitHub-hosted runners, Headless Chrome Three.js renders complex 3D scenes via SwiftShader CPU software emulation. At native 1080x1920 with MSAA 4x, 2048x2048 shadow maps, BokehPass, and UnrealBloomPass, rendering ~1,350 frames takes ~1.3s/frame (~29-31 minutes). The workflow's `timeout-minutes: 30` forcibly killed the runner before completion. Additionally, `subprocess.run(capture_output=True)` suppressed all stdout, creating a silent log black hole during the render.
- **Immediate Patch:** Optimized WebGL query string via `QS: "&res=0.75&aa=1&shadow=1024"`, reducing 3D pixel rasterization by 44% and shadow map size by 75% while keeping 2D text, badges, and captions native 1080x1920. Raised `timeout-minutes` to 60.
- **Architectural Mitigation:** Re-engineered `cloud_runner.py::run_cmd()` using streaming `subprocess.Popen` with `flush=True` and updated `capture.mjs` to emit `[render] frame X/N (Y%)` newlines, providing real-time telemetry to GitHub Actions.

---

### Incident ERR-012: GitHub Actions Expression Boolean Coercion on `workflow_dispatch` Dropdown Inputs
- **Date & Environment:** GitHub Actions Manual Trigger UI
- **Symptom:** When triggering manually with `workflow_dispatch` and selecting any slot (e.g. Slot 2, 3, 4, 5), the pipeline always ran Slot 1 or failed to resolve the slot properly.
- **Root Cause:** In GitHub Actions expression syntax, the `||` operator evaluates to a boolean rather than value coalescing. Expression `${{ inputs.slot || 'auto' }}` evaluated non-empty strings to `"true"`. When passed to `cloud_runner.py --slot "true"`, regex `re.match(r'(\d+)', "true")` failed, defaulting unconditionally to Slot 1.
- **Immediate Patch:** Passed input via standard POSIX environment expansion `INPUT_SLOT: ${{ inputs.slot }}` and invoked `--slot "${INPUT_SLOT:-auto}"`.
- **Architectural Mitigation:** Implemented `parse_slot_selection()` in `cloud_runner.py` with multi-format regex extraction and fallback protection, with full unit test coverage in `test_audit_suite.py`.

---

### Incident ERR-013: Top-of-the-Hour GitHub Queue Starvation & Concurrency Lockout
- **Date & Environment:** GitHub Actions Cron Scheduling Infrastructure
- **Symptom:** Scheduled executions were severely delayed (30–90 minutes) or silently dropped by GitHub Actions, appearing to never execute.
- **Root Cause:** Crons set to minute `0` (e.g. `0 3 * * *`, `0 7 * * *`) suffer extreme queuing delays due to global peak contention on GitHub Actions. Coupled with workflow-level `concurrency: group: daily-shorts, cancel-in-progress: false`, a 30-minute hanging job caused subsequent scheduled runs to be dropped by GitHub's concurrency ceiling (maximum 1 queued run).
- **Immediate Patch:** Offset all 5 daily crons by 10 minutes (`10 3 * * *`, `10 7 * * *`, `10 11 * * *`, `40 14 * * *`, `10 17 * * *`), bypassing the top-of-the-hour queue bottleneck.
- **Architectural Mitigation:** Refactored concurrency grouping to `${{ github.workflow }}-${{ github.ref }}-${{ github.event_name == 'push' && github.sha || 'singleton' }}` with `cancel-in-progress: true` on test commits, isolating push audits from scheduled video generation.

---

## 3. Failure Mode & Effects Analysis (FMEA) for Production

The following matrix assesses potential future failure modes, their severity, likelihood, and preventive mechanisms:

| Subsystem | Potential Failure Mode | Severity (1-5) | Likelihood (1-5) | Mitigation / Architectural Guardrail |
|---|---|:---:|:---:|---|
| **YouTube Data API** | Daily quota exhaustion (10,000 units/day ceiling reached). | **5** | 2 | 5 daily uploads consume 8,000 units ($5 \times 1600$). Throttled retries (`max_retries=1`) prevent consuming the remaining 2,000 unit buffer on failure. |
| **OAuth 2.0 Auth** | Refresh token revoked or expired after 6 months of inactivity. | **5** | 1 | Auth health check test detects token invalidation before rendering starts; alerts with standard error code. |
| **Whisper Alignment** | Audio hallucination or non-lexical words on obscure proper nouns. | **3** | 2 | `timing.js` has fallback logic: if a word is missing or misaligned, it calculates line-interpolated timestamps. |
| **Kokoro ONNX TTS** | Unexpected special characters or emojis causing phonemizer crash. | **4** | 2 | Text sanitization regex strips illegal non-ASCII punctuation before passing text to Kokoro. |
| **GitHub Actions** | Concurrency race condition on `_published.md` when pushing to `main`. | **3** | 3 | Git commit step uses `git pull --rebase origin main` with automatic retry before push. |
| **Storage / Disk** | Runner disk space exhaustion from uncompressed video frames. | **4** | 1 | Video rendering pipes frames directly to FFmpeg `stdin` (`image2pipe`), avoiding temporary frame dump to disk. |

---

## 4. Runbook & Standard Operating Procedures (SOP)

### How to Run Pre-Flight Diagnostics
Before triggering manual workflows or modifying code, execute the automated audit test suite locally:
```powershell
python -m unittest tests/test_audit_suite.py -v
```

### How to Manually Trigger a Specific Genre / Slot
1. Navigate to the **Actions** tab on GitHub: `https://github.com/honestlynotakb/AutoShort/actions`.
2. Select **Autonomous Daily YouTube Shorts** from the left panel.
3. Click **Run workflow**:
   - `auto` (automatically detects current slot based on time)
   - `1 - Geography & Flags (8:10 AM)`
   - `2 - Space & Cosmic (12:10 PM)`
   - `3 - Survival Scenarios (4:10 PM)`
   - `4 - Mind-Blowing Science (7:40 PM)`
   - `5 - Historic Torture (10:10 PM)`
4. Click the green **Run workflow** button.

### How to Re-Authenticate YouTube if Token is Revoked
If the YouTube API returns `invalid_grant`, re-run the local authorization tool:
```powershell
python cloud/get_youtube_token.py
```
Copy the printed `refresh_token` and update the `YOUTUBE_REFRESH_TOKEN` secret in **GitHub Repository Settings &rarr; Secrets and variables &rarr; Actions**.
