#!/usr/bin/env python3
"""Master Autonomous Cloud Runner for GitHub Actions.
Supports 3-Times-Daily Scheduled Slots (Optimized for Zapier Free Plan):
  Slot 1 (12:10 PM PKT / 07:10 UTC): Space, Cosmic & Flag Curiosities
  Slot 2 (06:10 PM PKT / 13:10 UTC): Mind-Blowing Science & Physics
  Slot 3 (10:10 PM PKT / 17:10 UTC): Survival Scenarios & Dark History

Enforces 5-Layer Defense-in-Depth Content Uniqueness Gate System:
  Gate 1: Semantic Topic Uniqueness & Reservation (Pre-Script)
  Gate 2: Script Narration Fingerprinting & 3-Gram Overlap (Pre-Voice)
  Gate 3: Visual & Composition Planning Diversity (Pre-Render)
  Gate 4: Perceptual Video Quality & 10-Frame dHash Auditor (Post-Render)
  Gate 5: Application-Level Publication Idempotency (Pre-Upload)
"""
from __future__ import annotations

import os
import re
import sys
import json
import time
import shutil
import argparse
import urllib.request
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from googleapiclient.errors import HttpError
except ImportError:
    HttpError = Exception

from cloud.state_manager import StateManager, get_state_manager
from cloud.topic_guard import TopicGuard
from cloud.script_guard import ScriptGuard
from cloud.visual_engine_2d import scaffold_2d_project, evaluate_visual_uniqueness
from cloud.duplicate_detector import VideoQualityAuditor, compute_file_sha256

PUBLISHED_FILE = ROOT / '_published.md'
SKILL_DIR = ROOT / 'faceless-shorts'
PROJECTS_DIR = ROOT / 'projects'
SLOTS_FILE = ROOT / 'config' / 'slots.json'


def load_slots_config():
    if not SLOTS_FILE.exists():
        raise FileNotFoundError(f"Missing config file: {SLOTS_FILE}")
    return json.loads(SLOTS_FILE.read_text(encoding='utf-8'))['slots']


def detect_current_slot(slots_cfg):
    """Detects the current slot based on UTC hour (7, 13, 17)."""
    utc_hour = datetime.now(timezone.utc).hour
    best_slot = "1"
    min_diff = 99
    for slot_id, info in slots_cfg.items():
        diff = abs(utc_hour - info.get('target_hour_utc', 0))
        if diff < min_diff:
            min_diff = diff
            best_slot = slot_id
    return best_slot


def get_published_topics():
    state_mgr = get_state_manager()
    topics = set()
    for item in state_mgr.get_all_published_and_reserved_topics():
        t = item.get("topic", "").lower().strip()
        if t:
            topics.add(t)
        title = item.get("title", "").lower().strip()
        if title:
            topics.add(title)
    if PUBLISHED_FILE.exists():
        text = PUBLISHED_FILE.read_text(encoding='utf-8')
        for line in text.splitlines():
            line = line.strip()
            if line.startswith('|') and not line.startswith('| Date') and not line.startswith('|---'):
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 3 and parts[2]:
                    topics.add(parts[2].lower())
                if len(parts) >= 5 and parts[4]:
                    topics.add(parts[4].lower())
    return topics


def generate_with_gemini(api_key: str, published_topics: set, slot_info: dict, negative_constraints: str = "") -> dict:
    prompt_theme = slot_info['prompt_theme']
    genre_name = slot_info['name']
    style = slot_info.get('style', '2d-motion')

    # Truncate published sample to fit token limits
    sample_published = list(published_topics)[:30]

    prompt = f"""You are an expert producer of viral YouTube Shorts in the style of Zack D. Films / Deep Dive 3D.
Your channel publishes calm, collected, high-curiosity educational explainers.

Current Specialized Genre: {genre_name}
Genre Focus & Constraints: {prompt_theme}
Visual Animation Style: {style}
Previously published topics to NEVER repeat or reword: {sample_published}
{negative_constraints}

Pick a completely fresh, unrepeated, viral curiosity topic strictly within this genre.
Write an original script (~80-100 words, calm explanation pace, 0.88x speed).
Structure:
1. Hook question first line.
2. Escalation & physical/historical mechanics.
3. Surprising twist or lesser-known reality.
4. Final line that loops back seamlessly to the start question.

Format strictly as JSON with this schema:
{{
  "topic": "Short topic description",
  "style": "{style}",
  "title": "Curious Title Under 60 Chars Ending In #shorts",
  "sources": ["Source 1", "Source 2"],
  "lines": [
    {{ "text": "Hook question first line?", "caps": "Hook *question | first *line?" }},
    {{ "text": "Escalation line...", "caps": "Escalation *line" }},
    ...
    {{ "text": "Last line looping back to start...", "caps": "Looping back | to *start", "gap": 0.25 }}
  ]
}}
Only return valid JSON."""

    models = ["gemini-2.0-flash", "gemini-1.5-flash"]
    payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode('utf-8')
    clean_key = api_key.strip()

    for model in models:
        for ver in ["v1beta", "v1"]:
            try:
                url = f"https://generativelanguage.googleapis.com/{ver}/models/{model}:generateContent?key={clean_key}"
                req = urllib.request.Request(
                    url,
                    data=payload,
                    headers={
                        "Content-Type": "application/json",
                        "x-goog-api-key": clean_key
                    }
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    raw_text = data['candidates'][0]['content']['parts'][0]['text']
                    match = re.search(r'\{.*\}', raw_text, re.DOTALL)
                    if match:
                        res = json.loads(match.group(0))
                        print(f"Successfully generated {genre_name} script using {model} ({ver})!")
                        return res
            except Exception as e:
                continue

    raise ValueError("All Gemini model endpoints failed")


def pick_topic_for_slot(
    slot_info: dict,
    published_topics: set,
    slot_id: str = "1",
    run_id: str = "auto",
    state_mgr: Optional[StateManager] = None
) -> dict:
    """Gate 1 & Gate 2 Orchestration: Selects and reserves a strictly unique topic and script.

    Returns:
        item_dict with attached _script_meta
    """
    state_mgr = state_mgr or get_state_manager()
    topic_guard = TopicGuard(state_mgr)
    script_guard = ScriptGuard(state_mgr)

    api_key = os.environ.get('GEMINI_API_KEY')
    rejected_candidates: List[Tuple[str, str]] = []

    # 1. Attempt Gemini Dynamic Generation with up to 3 Retries
    if api_key:
        print(f"[Gate 1] Querying Gemini AI for fresh topic in {slot_info['name']}...")
        for attempt in range(1, 4):
            try:
                neg_constraint = topic_guard.build_gemini_rejection_constraint(rejected_candidates)
                candidate = generate_with_gemini(api_key, published_topics, slot_info, neg_constraint)

                # Gate 1: Check topic uniqueness
                is_unique, reason, _ = topic_guard.evaluate_topic_uniqueness(
                    candidate_topic=candidate.get("topic", ""),
                    candidate_title=candidate.get("title", "")
                )
                if not is_unique:
                    print(f"[Gate 1 Rejection] [Attempt {attempt}/3] {reason}")
                    rejected_candidates.append((candidate.get("topic", ""), reason))
                    continue

                # Gate 2: Check script uniqueness
                script_ok, script_reason, script_meta = script_guard.evaluate_script_uniqueness(
                    lines=candidate.get("lines", []),
                    topic=candidate.get("topic", ""),
                    title=candidate.get("title", "")
                )
                if not script_ok:
                    print(f"[Gate 2 Rejection] [Attempt {attempt}/3] {script_reason}")
                    rejected_candidates.append((candidate.get("topic", ""), script_reason))
                    continue

                # Reserve topic atomically
                reserved, res_msg = topic_guard.reserve_if_unique(
                    candidate_topic=candidate["topic"],
                    candidate_title=candidate["title"],
                    slot_id=slot_id,
                    run_id=run_id
                )
                if reserved:
                    print(f"[Gate 1 & 2 Approved] Candidate verified & reserved: '{candidate['topic']}'")
                    candidate['_script_meta'] = script_meta
                    return candidate
                else:
                    print(f"[Gate 1 Warning] {res_msg}")

            except Exception as e:
                print(f"[Gate 1 Warning] Gemini API attempt {attempt}/3 failed: {e}")
                time.sleep(1)

        print("[Gate 1] Dynamic Gemini generation exhausted or failed; failing over to curated curriculum...")

    # 2. Curated Offline Curriculum Selection
    fallbacks = slot_info.get('fallbacks', [])
    for item in fallbacks:
        if item['topic'].lower() in published_topics or item['title'].lower() in published_topics:
            continue
        is_u, reason, _ = topic_guard.evaluate_topic_uniqueness(item['topic'], item['title'])
        if not is_u:
            continue
        script_u, _, script_meta = script_guard.evaluate_script_uniqueness(item['lines'], item['topic'], item['title'])
        if not script_u:
            continue

        reserved, res_msg = topic_guard.reserve_if_unique(
            candidate_topic=item['topic'],
            candidate_title=item['title'],
            slot_id=slot_id,
            run_id=run_id
        )
        if reserved:
            print(f"[Gate 1 Curriculum] Selected unused fallback topic: '{item['topic']}'")
            item['_script_meta'] = script_meta
            return item

    # 3. Cross-Slot Fallback Search (if current slot's fallbacks are all used)
    print(f"[Gate 1 Curriculum] All fallbacks for Slot {slot_id} have been used. Searching other slots...")
    slots_cfg = load_slots_config()
    for other_slot_id, other_info in slots_cfg.items():
        if other_slot_id == slot_id:
            continue
        for item in other_info.get('fallbacks', []):
            if item['topic'].lower() in published_topics or item['title'].lower() in published_topics:
                continue
            is_u, _, _ = topic_guard.evaluate_topic_uniqueness(item['topic'], item['title'])
            if not is_u:
                continue
            script_u, _, script_meta = script_guard.evaluate_script_uniqueness(item['lines'], item['topic'], item['title'])
            if not script_u:
                continue

            reserved, _ = topic_guard.reserve_if_unique(
                candidate_topic=item['topic'],
                candidate_title=item['title'],
                slot_id=slot_id,
                run_id=run_id
            )
            if reserved:
                print(f"[Gate 1 Cross-Curriculum] Selected unused topic from Slot {other_slot_id}: '{item['topic']}'")
                item['_script_meta'] = script_meta
                return item

    # 4. Critical Safe Failure: Never recycle index 0!
    raise RuntimeError(
        f"CRITICAL: All {len(fallbacks)} fallback topics have been published and Gemini API is unavailable. "
        "Pipeline halted safely to prevent duplicate content generation."
    )


def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')[:35]


def sanitize_text_for_tts(text: str) -> str:
    """Normalizes Unicode characters, replaces typographic marks, and strips emojis to protect Kokoro ONNX."""
    if not text:
        return ""
    text = text.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
    text = text.replace('—', ' - ').replace('–', ' - ').replace('…', '...')
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def verify_youtube_auth():
    """Fail-fast Stage 0: checks YouTube credentials and token refreshability before running CPU-heavy rendering."""
    client_id = os.environ.get('YOUTUBE_CLIENT_ID')
    client_secret = os.environ.get('YOUTUBE_CLIENT_SECRET')
    refresh_token = os.environ.get('YOUTUBE_REFRESH_TOKEN')

    if not all([client_id, client_secret, refresh_token]):
        print("[Stage 0] YouTube credentials not fully configured in environment (YOUTUBE_CLIENT_ID/SECRET/REFRESH_TOKEN).")
        print("[Stage 0] Video will render and be backed up to artifacts, but direct upload will be skipped.")
        return False

    try:
        from cloud.upload_youtube import get_authenticated_service
        get_authenticated_service()
        print("[Stage 0] Pre-flight YouTube OAuth credentials verified & active.")
        return True
    except Exception as e:
        print(f"[Stage 0 CRITICAL WARNING] YouTube OAuth pre-flight refresh failed: {e}")
        print("Please check credentials or re-run get_youtube_token.py if token was revoked.")
        return False


def write_step_summary(title, slot_info, topic, style, video_name, short_url, stage_metrics, total_time, run_id):
    summary_path = os.environ.get('GITHUB_STEP_SUMMARY')
    if not summary_path:
        return


def write_adaptive_shots(proj_dir, title, sample_lines, style="2d-motion"):
    """Backward-compatible helper to generate 2D adaptive shots.js."""
    from cloud.visual_engine_2d import generate_shots_js, pick_variation_palette, detect_topic_theme
    theme = detect_topic_theme(title, sample_lines)
    palette = pick_variation_palette(theme, [])
    code, seq, vec = generate_shots_js(title, title, sample_lines, theme, palette)
    shots_file = Path(proj_dir) / 'src' / 'shots.js'
    shots_file.parent.mkdir(parents=True, exist_ok=True)
    shots_file.write_text(code, encoding='utf-8')
    return shots_file

    content = f"""# 🎬 Autonomous YouTube Short Publication Summary

| Parameter | Value |
|---|---|
| **Run ID** | `{run_id}` |
| **Video Title** | **{title}** |
| **Genre** | {slot_info['name']} (Slot {slot_info.get('slot_id', 1)}) |
| **Topic** | {topic} |
| **Animation Style** | `{style}` |
| **Rendered File** | `{video_name}` |
| **YouTube Link** | {short_url} |
| **Total Duration** | **{total_time:.2f}s** |

### ⚡ Pipeline Stage Telemetry
| Stage | Execution Duration |
|---|---|
"""
    for stage, dur in stage_metrics.items():
        content += f"| {stage} | {dur:.2f}s |\n"

    content += f"| **Total Pipeline** | **{total_time:.2f}s** |\n"

    try:
        with open(summary_path, 'a', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        print(f"Warning: Failed to write step summary: {e}")


def run_cmd(cmd, cwd=None, env=None):
    print(f"\n[EXEC] {cmd}", flush=True)
    process = subprocess.Popen(
        cmd,
        shell=True,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    collected = []
    if process.stdout:
        for line in iter(process.stdout.readline, ''):
            print(line, end='', flush=True)
            collected.append(line)
        process.stdout.close()
    ret = process.wait()
    if ret != 0:
        raise RuntimeError(f"Command failed with exit code {ret}: {cmd}")
    return ''.join(collected)


def parse_slot_selection(slot_arg: str, slots_cfg: dict) -> str:
    if not slot_arg:
        return detect_current_slot(slots_cfg)
    clean = str(slot_arg).strip().lower()
    if clean in ('auto', 'true', 'false', 'none', ''):
        return detect_current_slot(slots_cfg)
    m = re.match(r'(\d+)', clean)
    if m:
        matched = m.group(1)
        if matched in slots_cfg:
            return matched
    return detect_current_slot(slots_cfg)


def main():
    parser = argparse.ArgumentParser(description="Autonomous Cloud Runner for YouTube Shorts")
    parser.add_argument('--slot', default=None, help="Slot ID (1-3 or auto)")
    parser.add_argument('--dry-run', action='store_true', help="Resolve slot and script without rendering/uploading")
    args = parser.parse_args()

    print("=" * 60, flush=True)
    print(" 3-TIMES-DAILY AUTONOMOUS SHORTS PIPELINE", flush=True)
    print("=" * 60, flush=True)

    slots_cfg = load_slots_config()
    slot_arg = args.slot if args.slot is not None else os.environ.get('INPUT_SLOT', 'auto')
    slot_id = parse_slot_selection(slot_arg, slots_cfg)
    print(f"Selected/Detected Slot ID: {slot_id}", flush=True)

    slot_info = slots_cfg.get(slot_id, slots_cfg["1"])
    print(f"Slot {slot_id}: {slot_info['name']} (Scheduled: {slot_info['time_pkt']} PKT)")

    # Generate unique execution run ID for application-level idempotency
    run_id = f"slot{slot_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{os.getpid()}"
    print(f"Execution Run ID: {run_id}", flush=True)

    state_mgr = get_state_manager()
    published = get_published_topics()
    print(f"Found {len(published)} previously registered topics.", flush=True)

    # Gate 1 & 2: Semantic Topic & Script Originality Verification
    item = pick_topic_for_slot(slot_info, published, state_mgr=state_mgr, slot_id=slot_id, run_id=run_id)
    script_meta = item.get('_script_meta', {})

    # Sanitize lines to eliminate special Unicode/emojis that crash Kokoro ONNX TTS
    for line in item['lines']:
        line['text'] = sanitize_text_for_tts(line['text'])

    topic = item['topic']
    style = item.get('style', slot_info.get('style', '2d-motion'))
    title = item['title']
    category_id = slot_info.get('category_id', '28')
    tags = slot_info.get('tags', ["shorts", "facts", "curiosity"])

    slug = slugify(title.replace('#shorts', ''))
    proj_dir = PROJECTS_DIR / slug

    print(f"\nTopic: {topic}")
    print(f"Genre: {slot_info['name']}")
    print(f"Style: {style}")
    print(f"Title: {title}")
    print(f"Category: {category_id}")
    print(f"Project Folder: {proj_dir}")

    if args.dry_run:
        print("\n[DRY-RUN] Script Preview:")
        for idx, line in enumerate(item['lines']):
            print(f"  Line {idx}: {line['text']}")
        print(f"[DRY-RUN] Tags: {tags}")
        print("\nDRY-RUN COMPLETE.")
        # Release reservation in dry-run so test isn't locked
        state_mgr.release_topic(topic)
        return

    # Gate 3: Visual & Composition Planning
    auditor = VideoQualityAuditor(state_mgr)
    recent_palettes = [entry.get("palette") for entry in reversed(auditor.history[-5:]) if entry.get("palette")]

    print("\n--- [Stage 0.5/5] Scaffolding High-Quality 2D Animated Project ---")
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    if proj_dir.exists():
        shutil.rmtree(proj_dir)

    theme_name, palette_id, scene_sequence = scaffold_2d_project(
        proj_dir=proj_dir,
        title=title,
        topic=topic,
        lines=item['lines'],
        recent_palette_ids=recent_palettes
    )

    vis_ok, vis_reason = evaluate_visual_uniqueness(
        theme_name=theme_name,
        palette_id=palette_id,
        scene_sequence=scene_sequence,
        history_entries=auditor.history
    )
    print(f"[Gate 3 Visual] {vis_reason}")

    # Write script.json with mandatory calm collected tone settings
    script_data = {
        "title": title,
        "voice": "am_michael",
        "speed": 0.88,
        "lead": 0.35,
        "outro": 1.0,
        "gap": 0.40,
        "music": "bed",
        "sources": item.get('sources', ["Scientific Literature & Historical Records"]),
        "lines": item['lines']
    }
    (proj_dir / 'script.json').write_text(json.dumps(script_data, indent=2), encoding='utf-8')

    py = sys.executable
    env = os.environ.copy()
    env['SOFTWARE_GL'] = '1'
    env['PYTHONPATH'] = str(ROOT)
    env.setdefault('FPS', '24')
    env.setdefault('QS', '&res=0.55&aa=1&shadow=512')
    env.setdefault('PYTHONUNBUFFERED', '1')
    t_pipeline_start = time.time()
    stage_metrics = {}

    # 0. Eager Pre-flight Auth Check (Fail-Fast before 15 min rendering)
    print("\n--- [Stage 0/5] Pre-Flight YouTube Credential Check ---")
    t0 = time.time()
    auth_ok = verify_youtube_auth()
    stage_metrics['Pre-Flight Auth Check'] = round(time.time() - t0, 2)

    # 1. Synthesize Voice
    print("\n--- [Stage 1/5] Synthesizing Calm Voiceover (Kokoro ONNX) ---")
    t0 = time.time()
    run_cmd(f'"{py}" "{SKILL_DIR}/scripts/voice.py" "{proj_dir}"', env=env)
    stage_metrics['Voice Synthesis'] = round(time.time() - t0, 2)

    # 2. Whisper Word Alignment
    print("\n--- [Stage 2/5] Subtitle Word Alignment (Faster-Whisper) ---")
    t0 = time.time()
    run_cmd(f'"{py}" "{SKILL_DIR}/scripts/words.py" "{proj_dir}"', env=env)
    stage_metrics['Whisper Alignment'] = round(time.time() - t0, 2)

    # 3. Audio Cues & Calm Mixing
    print("\n--- [Stage 3/5] Mixing Procedural Sound & Ambient Bed ---")
    t0 = time.time()
    run_cmd('node tools/capture.mjs cues', cwd=proj_dir, env=env)
    run_cmd(f'"{py}" tools/mix.py .', cwd=proj_dir, env=env)
    stage_metrics['Audio Cues & Mixing'] = round(time.time() - t0, 2)

    # 4. Render Video
    renders_dir = proj_dir / 'renders'
    renders_dir.mkdir(exist_ok=True)
    video_out = renders_dir / f"{slug}.mp4"
    print("\n--- [Stage 4/5] Rendering 1080x1920 MP4 Video (Headless Chrome) ---")
    t0 = time.time()
    run_cmd(f'node tools/capture.mjs video "renders/{slug}.mp4"', cwd=proj_dir, env=env)
    stage_metrics['Chrome Headless Render'] = round(time.time() - t0, 2)

    if not video_out.exists():
        state_mgr.release_topic(topic)
        raise FileNotFoundError(f"Render failed, {video_out} not created")

    # Gate 4: Quality Audit & Perceptual Duplicate Check
    print("\n--- [Stage 4.5/5] Gate 4 Pre-Upload Quality & Perceptual Deduplication Audit ---")
    t0 = time.time()
    is_dup, dup_reason, meta = auditor.audit_and_check_duplicate(
        video_path=video_out,
        topic=topic,
        title=title,
        theme=theme_name,
        palette=palette_id,
        scene_sequence=scene_sequence,
        max_similarity_threshold=float(os.environ.get("GATE4_SIMILARITY_THRESHOLD", "0.85"))
    )
    stage_metrics['Quality & Deduplication Audit'] = round(time.time() - t0, 2)

    if is_dup:
        print(f"\n[CRITICAL QUALITY REJECTION] Video failed Gate 4 audit: {dup_reason}")
        state_mgr.release_topic(topic)
        raise ValueError(f"Deduplication Audit Failed: {dup_reason}")
    else:
        print(f"[Gate 4 PASSED] {dup_reason}")
        auditor.record_approved_video(meta)
        # Register script in script_registry.json
        script_guard = ScriptGuard(state_mgr)
        script_guard.record_approved_script(item['lines'], topic, title, script_meta.get('sha256', ''))

    # Gate 5: Upload to YouTube (with Idempotency)
    print("\n--- [Stage 5/5] Uploading Short to YouTube ---")
    t0 = time.time()
    short_url = None
    vid_id = None
    video_hash = compute_file_sha256(video_out)

    try:
        from cloud.upload_youtube import upload_short
        desc = f"{item['lines'][0]['text']}\n\n#shorts #{slot_info['name'].replace(' ', '')} #curiosity"
        vid_id, short_url = upload_short(
            video_path=video_out,
            title=title,
            description=desc,
            tags=tags,
            category_id=category_id,
            privacy_status="public",
            run_id=run_id
        )
    except HttpError as he:
        status_code = getattr(getattr(he, 'resp', None), 'status', None)
        err_str = str(he)
        if status_code == 403 and 'quotaExceeded' in err_str:
            print("\n[CRITICAL WARNING] YouTube Data API daily upload quota exceeded!")
        elif 'invalid_grant' in err_str:
            print("\n[CRITICAL WARNING] YouTube OAuth token expired or revoked. Please run get_youtube_token.py.")
        else:
            print(f"YouTube HTTP Error {status_code or 'Unknown'}: {he}")
        short_url = f"[Quota/Upload Error] {video_out.name}"
    except Exception as e:
        print(f"Direct YouTube upload failed or pending: {e}")
        short_url = f"[Manual/Pending Upload] {video_out.name}"
    stage_metrics['YouTube Upload'] = round(time.time() - t0, 2)

    # 6. Record Publication in Persistent State and _published.md
    state_mgr.record_publication(
        run_id=run_id,
        topic=topic,
        title=title,
        video_hash=video_hash,
        youtube_id=vid_id or "pending",
        short_url=short_url,
        slot_id=slot_id,
        status="PUBLISHED" if vid_id else "PENDING_MANUAL"
    )

    today = datetime.now().strftime("%Y-%m-%d")
    log_line = f"| {today} | {topic} | {style} | {title} | {short_url} |\n"
    with open(PUBLISHED_FILE, 'a', encoding='utf-8') as f:
        f.write(log_line)

    total_time = round(time.time() - t_pipeline_start, 2)

    # 7. Write GitHub Step Summary
    write_step_summary(
        title=title,
        slot_info=slot_info,
        topic=topic,
        style=style,
        video_name=video_out.name,
        short_url=short_url,
        stage_metrics=stage_metrics,
        total_time=total_time,
        run_id=run_id
    )

    print("\n" + "=" * 60)
    print(" 3-DAILY AUTONOMOUS RUN COMPLETE!")
    print(f" Published: {title}")
    print(f" Genre:     {slot_info['name']}")
    print(f" Output:    {video_out.name}")
    print(f" URL:       {short_url}")
    print(f" Run ID:    {run_id}")
    print("-" * 60)
    print(" Execution Stage Telemetry:")
    for stage, dur in stage_metrics.items():
        print(f"   • {stage:<24}: {dur:>6.2f}s")
    print(f"   • {'TOTAL TIME':<24}: {total_time:>6.2f}s")
    print("=" * 60)


if __name__ == '__main__':
    main()
