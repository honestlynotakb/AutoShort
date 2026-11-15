# Autonomous YouTube Shorts Cloud Pipeline — Project Handoff

**Target Channel:** Ayaan Kashif (`UCHNvsA_nL4uSyZIr8RX9Zyw`)  
**Repository:** `honestlynotakb/AutoShort` (Branch: `main`)  
**System Status:** 🟢 Production Ready (41/41 Automated Audit Tests Passing)  
**Date of Handoff:** November 15, 2026  
**Architecture Version:** 3.0 (Permanent 5-Layer Content Uniqueness & State Persistence Architecture)  

---

## 1. Executive Summary & System Mission

The **Autonomous YouTube Shorts Cloud Pipeline** is a 100% serverless, zero-cost, end-to-end autonomous video generation and publication infrastructure running entirely on **GitHub Actions**. It operates independently of any local machine — generating, voicing, animating, rendering, and publishing faceless YouTube Shorts even when local workstations are powered off.

### Key Capabilities
- **Curated Multi-Genre Schedule:** Automated publishing 3 times daily (Space/Cosmic, Mind-Blowing Science, Survival Scenarios & Dark History).
- **5-Layer Content Uniqueness Defense:** Comprehensive gate system blocking duplicates before script generation, before voice synthesis, before rendering, after rendering, and immediately before YouTube upload.
- **Dual Dynamic/Offline Topic Engine:** Uses a cascading Gemini model pool (`gemini-2.0-flash`, `gemini-1.5-flash`) with negative constraint feedback loops, backed by an expanded **45-topic curated offline curriculum** (15 verified topics per slot).
- **AI Voice & Subtitle Sync:** Kokoro ONNX neural TTS at a calm 0.88x speed with Faster-Whisper word-by-word dynamic animated subtitles.
- **Dynamic 2D Motion Graphics Engine:** Procedural SVG/Canvas motion graphics, HUD gauges, 12 subject-aware focal vectors, cutaway diagrams, and kinetic typography.
- **Multi-Tiered Deduplication:** Pre-upload 10-frame dHash perceptual hashing against full history, SHA-256 fingerprinting, Jaccard token overlap ($\ge 0.55$), and SequenceMatcher similarity ($\ge 0.70$).
- **Unified Persistent State Management:** Atomic JSON persistence in `cloud/state/` tracking topics, script hashes, video fingerprints, and upload idempotency records across ephemeral GitHub Actions runners.
- **Dual Publication Strategy:** Direct YouTube Data API v3 upload + GitHub Release & direct media hosting for Zapier automation (staying within free tier limits: 90 tasks/month).

---

## 2. Architecture & The 5-Layer Defense Gate System

Every scheduled or dispatched run executes a multi-gate verification pipeline:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    5-LAYER CONTENT UNIQUENESS GATE PIPELINE                     │
└─────────────────────────────────────────────────────────────────────────────────┘
                                       │
     [Stage 0: Pre-Flight Check] ◄─────┴─────► [Slot Auto-Detection]
       - Verify OAuth & API credentials          - Match UTC hour to Slot 1, 2, or 3
       - Load persistent state from cloud/state/ - Generate unique Run ID
                                       │
                                       ▼
     [GATE 1: Semantic Topic Uniqueness & Reservation]
       - Check exact normalized string against topic_registry.json
       - Check case, whitespace, and punctuation variations
       - Check content token Jaccard overlap (rejection threshold >= 0.55)
       - Check SequenceMatcher ratio (rejection threshold >= 0.70 with keyword overlap)
       - Prompt Gemini with negative constraints on retry (up to 3 attempts)
       - If offline: iterate 15 curated slot fallbacks; cross-slot search if needed
       - Fail safely without duplicate fallback loops
       - Atomically reserve topic with Run ID in topic_registry.json
                                       │
                                       ▼
     [GATE 2: Script Narration Originality]
       - Normalize narration text & compute SHA-256 fingerprint
       - Extract word 3-grams & compute Jaccard overlap (threshold >= 0.50 rejected)
       - Check line-by-line similarity to prevent template recycling
       - If rejected, regenerate before any voice or audio compute
                                       │
                                       ▼
     [GATE 3: Visual & Composition Planning Diversity]
       - Route topic subject matter to 12 procedural vector archetypes:
         (Black hole, Neutron star, Planetary orbit, Asteroids, Lattice, Molecules,
          Prism refraction, Quicksand, Submerged cabin, Acoustic chamber, Thermal, Compass)
       - Pre-render check: ensure theme, palette, and archetypes differ from predecessor
       - Cycle non-repeating color palettes
                                       │
                                       ▼
     [Stage 1-3: Synthesis, Alignment & Audio Mix]
       - Neural TTS: Kokoro ONNX (am_michael, 0.88x speed)
       - Subtitle Alignment: Faster-Whisper (small.en)
       - Audio Mix: Procedural cues + ambient bed (mix.py)
                                       │
                                       ▼
     [Stage 4: Headless Video Rendering]
       - Headless Google Chrome + Node.js 22 (SwiftShader CPU GL)
       - Native 1080x1920 MP4 at 24 FPS with piped FFmpeg stream
                                       │
                                       ▼
     [GATE 4: Perceptual Video Quality & Full-History dHash Auditor]
       - Extract 10 equidistant frames (filtering out black/solid frames)
       - Compute 64-bit dHash on each frame + exact video file SHA-256
       - Evaluate normalized Hamming distance across ALL historical entries
       - Reject if similarity >= 0.78 (releasing topic reservation)
       - Record approved video in video_history.json & script in script_registry.json
                                       │
                                       ▼
     [GATE 5: Publication Idempotency & Reconciliation]
       - Check publication_history.json: has video SHA-256 or Run ID already published?
       - If published: skip duplicate API upload; reuse confirmed YouTube publication
       - If clean: execute resumable YouTube upload & GitHub Release for Zapier
       - Atomically record publication in publication_history.json
       - Append to _published.md
       - Commit & push _published.md AND cloud/state/*.json in GitHub Actions
```

---

## 3. Daily Slot Schedule & Zapier Budget

The schedule is calibrated to Pakistan Standard Time (PKT, UTC+5) and strictly budgeted to remain under the Zapier Free Tier limit (100 tasks/month).

| Slot | Scheduled Time (PKT) | Cron Expression (UTC) | Target Hour (UTC) | Content Theme / Focus | Category ID | Visual Engine | Curated Fallbacks |
|:---:|:---:|:---:|:---:|:---|:---:|:---:|:---:|
| **Slot 1** | **12:10 PM PKT** | `10 7 * * *` | 07:00 UTC | Space, Cosmic & Flag Curiosities | `28` (Sci & Tech) | `2d-motion` | 15 Topics |
| **Slot 2** | **06:10 PM PKT** | `10 13 * * *` | 13:00 UTC | Mind-Blowing Science & Physics | `28` (Sci & Tech) | `2d-motion` | 15 Topics |
| **Slot 3** | **10:10 PM PKT** | `10 17 * * *` | 17:00 UTC | Survival Scenarios & Dark History | `27` (Education) | `2d-motion` | 15 Topics |

$$\text{Task Consumption} = 3 \text{ uploads/day} \times 30 \text{ days} = 90 \text{ tasks/month} \quad (\le 100 \text{ monthly limit})$$

---

## 4. Key File & Directory Inventory

| File / Directory Path | Role & Description |
|---|---|
| `cloud/state_manager.py` | Unified persistent state management layer with atomic writes (`.tmp` + `os.replace`), schema versioning, and reservation lifecycles. |
| `cloud/topic_guard.py` | Gate 1 semantic topic uniqueness engine (exact, normalized, token Jaccard, SequenceMatcher, and negative constraint builder). |
| `cloud/script_guard.py` | Gate 2 script narration originality auditor (SHA-256 fingerprinting, word 3-gram overlap, and line-by-line template detection). |
| `cloud/visual_engine_2d.py` | Gate 3 subject-aware procedural visual engine with 12 distinct focal vector archetypes, varied backgrounds, and palette cycling. |
| `cloud/duplicate_detector.py` | Gate 4 perceptual video quality auditor with 10-frame 64-bit dHash extraction, black frame filtering, and full-history comparison. |
| `cloud/upload_youtube.py` | Gate 5 YouTube Data API v3 client with pre-upload idempotency verification and state reconciliation. |
| `cloud/cloud_runner.py` | Master orchestration controller executing Gates 1 through 5, slot routing, rendering, and telemetry. |
| `config/slots.json` | Master slot definitions with expanded 45-topic curated offline curriculum (15 verified topics per slot). |
| `tests/test_audit_suite.py` | 41-test comprehensive automated regression suite verifying all gates, tiers, edge cases, and deduplication invariants. |
| `.github/workflows/daily-shorts.yml` | GitHub Actions workflow controlling crons, test suite gate, render job, and state persistence commit. |
| `ERROR_AUDIT_LOG.md` | Living post-mortem registry and FMEA detailing Incidents ERR-001 through ERR-017. |
| `_published.md` | Persistent markdown ledger recording every published Short and YouTube URL. |

---

## 5. Required Secrets & Configuration

Add these in **GitHub Repository Settings &rarr; Secrets and variables &rarr; Actions**:

| Secret Name | Purpose | Mandatory? | Notes |
|---|---|:---:|---|
| `YOUTUBE_CLIENT_ID` | Google Cloud OAuth Client ID | **Yes** | Web/Desktop application credential from GCP. |
| `YOUTUBE_CLIENT_SECRET` | Google Cloud OAuth Client Secret | **Yes** | Matching secret from GCP console. |
| `YOUTUBE_REFRESH_TOKEN` | Long-lived YouTube OAuth Refresh Token | **Yes** | Generated via `python cloud/get_youtube_token.py`. |
| `GEMINI_API_KEY` | Google Generative AI API Key | Optional | Powers infinite dynamic scripts. If omitted, falls back safely to `config/slots.json`. |
| `GITHUB_TOKEN` | Repository Access Token | Automatic | Provided natively by GitHub Actions runner (`contents: write`). |

---

## 6. Standard Operating Procedures (SOP) & Runbook

### 6.1 Running Pre-Flight Diagnostics Locally
Execute the automated audit test suite locally before pushing code changes:
```powershell
python -m unittest tests/test_audit_suite.py -v
```
*Expected Result:* 41 tests passing in ~2.5 seconds with 0 failures and 0 errors.

### 6.2 Executing Local Dry Runs (Verifying Topic Uniqueness)
Simulate script generation and slot resolution without rendering video:
```powershell
# Simulate Slot 1 (Space & Cosmic)
python cloud/cloud_runner.py --slot 1 --dry-run

# Simulate Slot 2 (Science & Physics)
python cloud/cloud_runner.py --slot 2 --dry-run

# Simulate Slot 3 (Survival & History)
python cloud/cloud_runner.py --slot 3 --dry-run
```

### 6.3 Triggering a Manual Cloud Generation
1. Open the repository on GitHub: `https://github.com/honestlynotakb/AutoShort/actions`.
2. Select **Autonomous Daily YouTube Shorts** from the left panel.
3. Click the **Run workflow** dropdown:
   - Select `auto` for time-of-day automatic routing, or pick Slot 1, 2, or 3 specifically.
4. Click the green **Run workflow** button.

---

## 7. Permanent Architectural Guardrails & Invariants

1. **State Persistence in Ephemeral Runners:** `.github/workflows/daily-shorts.yml` commits both `_published.md` AND `cloud/state/*.json` to ensure topic registrations, script hashes, video fingerprints, and publication records survive across independent runner executions.
2. **Never Recycle Fallback Index 0:** If all fallbacks in a slot have been published and Gemini API is unavailable, the engine searches other slots; if all 45 fallbacks in the repository are exhausted, it raises an explicit `RuntimeError` and halts safely rather than duplicating content.
3. **Pre-Compute Uniqueness Gating:** Candidates are rejected at Gate 1 (Topic) and Gate 2 (Script) *before* expensive voice synthesis or 30-minute Chrome rendering begins.
4. **Application-Level Idempotency:** Duplicate uploads from workflow reruns or interrupted uploads are prevented by validating both the video file SHA-256 and the execution `run_id` before initiating YouTube Data API requests.
5. **Universal LF Line Endings & Atomic Writes:** Atomic replacement (`os.replace` with Windows handle retry) and `.gitattributes` enforce zero-corruption state persistence.
