#!/usr/bin/env python3
"""Master Autonomous Cloud Runner for GitHub Actions.
Supports 5-Times-Daily Scheduled Slots:
  Slot 1 (08:00 AM PKT / 03:00 UTC): Geography & Flag Knowledge
  Slot 2 (12:00 PM PKT / 07:00 UTC): Space & Cosmic What-Ifs
  Slot 3 (04:00 PM PKT / 11:00 UTC): Survival & Extreme Scenarios
  Slot 4 (07:30 PM PKT / 14:30 UTC): Mind-Blowing Science & Physics
  Slot 5 (10:00 PM PKT / 17:00 UTC): Historic Torture Techniques & Bizarre History
"""
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

ROOT = Path(__file__).resolve().parent.parent
PUBLISHED_FILE = ROOT / '_published.md'
SKILL_DIR = ROOT / 'faceless-shorts'
PROJECTS_DIR = ROOT / 'projects'
SLOTS_FILE = ROOT / 'config' / 'slots.json'

def load_slots_config():
    if not SLOTS_FILE.exists():
        raise FileNotFoundError(f"Missing config file: {SLOTS_FILE}")
    return json.loads(SLOTS_FILE.read_text(encoding='utf-8'))['slots']

def detect_current_slot(slots_cfg):
    """Detects the current slot based on UTC hour (3, 7, 11, 14, 17)."""
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
    if not PUBLISHED_FILE.exists():
        return set()
    text = PUBLISHED_FILE.read_text(encoding='utf-8')
    topics = set()
    for line in text.splitlines():
        if line.startswith('|') and not line.startswith('| Date') and not line.startswith('|---'):
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 3:
                topics.add(parts[2].lower())
                if len(parts) >= 5:
                    topics.add(parts[4].lower())
    return topics

def generate_with_gemini(api_key, published_topics, slot_info):
    prompt_theme = slot_info['prompt_theme']
    genre_name = slot_info['name']
    style = slot_info.get('style', 'deep-dive')

    prompt = f"""You are an expert producer of viral YouTube Shorts in the style of Zack D. Films / Deep Dive 3D.
Your channel publishes calm, collected, high-curiosity educational explainers.

Current Specialized Genre: {genre_name}
Genre Focus & Constraints: {prompt_theme}
Visual Animation Style: {style}
Previously published topics to NEVER repeat: {list(published_topics)}

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

    models = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]
    payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode('utf-8')

    for model in models:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            req = urllib.request.Request(
                url,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": api_key.strip()
                }
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                raw_text = data['candidates'][0]['content']['parts'][0]['text']
                match = re.search(r'\{.*\}', raw_text, re.DOTALL)
                if match:
                    res = json.loads(match.group(0))
                    print(f"Successfully generated {genre_name} script using {model}!")
                    return res
        except Exception as e:
            print(f"Gemini model {model} attempt failed: {e}")
            continue

    raise ValueError("All Gemini model endpoints failed")

def pick_topic_for_slot(slot_info, published_topics):
    api_key = os.environ.get('GEMINI_API_KEY')
    if api_key:
        try:
            print(f"Querying Gemini API for genre: {slot_info['name']}...")
            return generate_with_gemini(api_key, published_topics, slot_info)
        except Exception as e:
            print(f"Gemini API generation failed ({e}), falling back to slot curriculum...")

    fallbacks = slot_info.get('fallbacks', [])
    for item in fallbacks:
        if item['topic'].lower() not in published_topics and item['title'].lower() not in published_topics:
            return item

    if fallbacks:
        return fallbacks[0]

    # Generic emergency fallback
    return {
        "topic": f"Curiosity explainer in {slot_info['name']}",
        "style": slot_info.get('style', 'deep-dive'),
        "title": f"The Truth Behind {slot_info['name']} #shorts",
        "sources": ["Scientific Literature & Historical Records"],
        "lines": [
            {"text": f"Have you ever wondered about the biggest mystery in {slot_info['name']}?", "caps": f"The *mystery | of *{slot_info['name'][:12]}"},
            {"text": "Under the surface, physical laws and human history combine in unexpected ways.", "caps": "Physical *laws | in *unexpected ways"},
            {"text": "Scientists and historians have spent decades unraveling this exact paradox.", "caps": "Decades of *research | on this *paradox"},
            {"text": "So remember to look closer next time before you explore...", "caps": "Look *closer | before you *explore", "gap": 0.25}
        ]
    }

def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')[:35]

def write_adaptive_shots(proj_dir, title, lines, style):
    shots_js_path = proj_dir / 'src' / 'shots.js'
    num_lines = len(lines)
    clean_title = title.replace('#shorts', '').strip()
    shot_blocks = []

    for i in range(num_lines):
        shot_id = f"S{i+1:02d}"
        if i == 0:
            block = f"""
  {{ const st = cut({i});
    add({{ id: '{shot_id}', at: st, note: 'Hook: Hero pushes in with curiosity', draw(lt, d, t, blit) {{
      reset();
      const k = eo(clamp(lt / d));
      hero.pose({{ head: [-8 * k + 4 * Math.sin(lt * 2), 4, 0], spine: [-3 * k, 0, 0], lid: -0.2, look: [0, -3 * k] }});
      cam.position.copy(lerpV(V3(0.42, 1.72, 0.45), V3(0.25, 1.7, 0.15), eio(lt / d)));
      cam.lookAt(FACE);
      kitchenRender(cam.position.distanceTo(FACE));
      blit();
      pill('{clean_title.upper()[:22]}', 540, 340, eob(seg(lt, 0.15, 0.45)), '#FFD43B');
    }} }});
    cue(st, 'whoosh'); cue(st + 0.2, 'pop', {{ gain: 0.6 }}); }}"""
        elif i == num_lines - 1:
            block = f"""
  {{ const st = cut({i});
    add({{ id: '{shot_id}', at: st, note: 'Outro: Hero looks at camera, warning sign', draw(lt, d, t, blit) {{
      reset();
      hero.pose({{ head: [-2, 0, 0], lid: 0.05, look: [0, 0] }});
      cam.position.copy(lerpV(V3(0.0, 1.62, 0.9), V3(0.05, 1.64, 0.55), eio(lt / d)));
      cam.lookAt(FACE);
      kitchenRender(cam.position.distanceTo(FACE));
      blit();
      warning(540, 1150, eob(seg(lt, 0.25, 0.55)) * 0.95);
      pill('DID YOU KNOW THIS?', 540, 340, eob(seg(lt, 0.2, 0.45)), '#FFD43B');
    }} }});
    cue(st, 'whoosh'); cue(st + 0.25, 'slam', {{ gain: 0.7 }}); }}"""
        else:
            mode = i % 4
            if mode == 1:
                block = f"""
  {{ const st = cut({i});
    add({{ id: '{shot_id}', at: st, note: 'X-ray inspection view', draw(lt, d, t, blit) {{
      reset();
      lungs(1 + Math.sin(lt * 3) * 0.05);
      chest(xh, 1);
      xh.pose({{ head: [4, -6, 0] }});
      cam.position.copy(lerpV(V3(0.55, 1.5, 1.6), V3(0.3, 1.42, 1.1), eio(lt / d)));
      cam.lookAt(0, 1.33, 0);
      E.render(X.scene, cam, {{ ...XLOOK, focus: cam.position.distanceTo(V3(0, 1.33, 0)) }});
      blit();
      pill('KEY EVIDENCE', 540, 340, eob(seg(lt, 0.2, 0.45)), '#4FD1E8');
    }} }});
    cue(st, 'whoosh'); cue(st + 0.15, 'thud', {{ gain: 0.45 }}); }}"""
            elif mode == 2:
                block = f"""
  {{ const st = cut({i});
    add({{ id: '{shot_id}', at: st, note: 'Macro detail view', draw(lt, d, t, blit) {{
      VS.update(t, -lt * 1.6, 0, 0);
      cam.position.set(0, 0, -lt * 1.6);
      cam.lookAt(0.15, -0.08, -lt * 1.6 - 5);
      E.render(VS.scene, cam, VLOOK);
      blit();
      pill('DETAILED REALITY', 540, 340, eob(seg(lt, 0.15, 0.4)), '#7CF29A');
    }} }});
    cue(st, 'whoosh'); cue(st + 0.2, 'pop', {{ gain: 0.5 }}); }}"""
            elif mode == 3:
                block = f"""
  {{ const st = cut({i});
    add({{ id: '{shot_id}', at: st, note: 'Dynamic tension view', draw(lt, d, t, blit) {{
      reset();
      const p = 0.5 + 0.5 * Math.sin(lt * 8);
      I.heart.scale.setScalar(1 + p * 0.15);
      I.heart.material.emissiveIntensity = 0.2 + p * 0.7;
      const H0 = V3(0.025, 1.41, 0.07);
      cam.position.copy(lerpV(V3(0.25, 1.48, 0.62), V3(0.12, 1.44, 0.42), eio(lt / d)));
      cam.lookAt(H0);
      E.render(X.scene, cam, {{ ...XLOOK, bloom: 0.6, focus: cam.position.distanceTo(H0) }});
      blit();
      pill('CRITICAL POINT', 540, 340, eob(seg(lt, 0.2, 0.45)), '#FF8A8A');
    }} }});
    cue(st, 'whoosh'); cue(st + 0.2, 'heartbeat'); }}"""
            else:
                block = f"""
  {{ const st = cut({i});
    add({{ id: '{shot_id}', at: st, note: 'Medium shot reaction', draw(lt, d, t, blit) {{
      reset();
      hero.pose({{ head: [2, -6 + Math.sin(lt * 2) * 3, 0], lid: -0.15, look: [6, 0] }});
      const a = lerp(0.55, 0.2, eio(lt / d));
      cam.position.set(0.1 + Math.sin(a) * 2.1, 1.45, -0.6 + Math.cos(a) * 2.1);
      cam.lookAt(0.1, 1.25, -0.6);
      kitchenRender(2.1);
      blit();
      pill('SURPRISING TWIST', 540, 340, eob(seg(lt, 0.2, 0.45)), '#C9D6DD');
    }} }});
    cue(st, 'whoosh'); cue(st + 0.2, 'pop', {{ gain: 0.5 }}); }}"""
        shot_blocks.append(block)

    shots_content = f"""// Adaptive shots for: {title}
import * as THREE from 'three';
import {{ ctx, W, H, clamp, lerp, seg, eo, eio, eob }} from './core/lib.js';
import {{ L, Wd, T }} from './core/timing.js';
import {{ camera }} from './core/engine.js';
import {{ Human }} from './core/human.js';
import * as SETS from './core/sets.js';
import {{ label, pill, warning, blackout }} from './core/look2d.js';

const V3 = (x, y, z) => new THREE.Vector3(x, y, z);
const lerpV = (a, b, k) => a.clone().lerp(b, k);
function screen(p, cam) {{ const v = p.clone().project(cam); return [(v.x + 1) / 2 * W, (1 - v.y) / 2 * H]; }}

export function buildShots(E) {{
  const S = [], CUES = [], add = (o) => (S.push(o), o), cue = (t, type, o = {{}}) => CUES.push({{ t: +t.toFixed(3), type, ...o }});
  const cut = (i) => (i === 0 ? 0 : L(i) - 0.08);
  const cam = camera(30);
  const KLOOK = {{ aperture: 0.003, maxblur: 0.01, bloom: 0.2 }}, XLOOK = {{ aperture: 0.0015, bloom: 0.55, bloomThreshold: 0.4, vignette: 0.45 }}, VLOOK = {{ aperture: 0.005, maxblur: 0.012, bloom: 0.6, bloomThreshold: 0.5, focus: 3.2 }};

  const K = SETS.kitchen(E), hero = new Human({{}}); hero.group.position.set(0.1, 0, -0.6); K.scene.add(hero.group);
  const X = SETS.xrayStage(E), xh = new Human({{}}), xmat = SETS.xrayMaterial(); xh.setBodyMaterial(xmat); const I = SETS.insides(); xh.spine.add(I.group); X.scene.add(xh.group);
  const VS = SETS.vessel(E);
  const CYAN = new THREE.Color('#4FD1E8'), RED = new THREE.Color('#FF3B3B');
  const chest = (h, k) => h.parts[0].scale.set(1 + 0.03 * k, 1 + 0.012 * k, 1 + 0.08 * k);
  const lungs = (k) => I.lungs.forEach((l) => l.scale.set(1 + 0.12 * k, 1 + 0.1 * k, 1 + 0.12 * k));
  const reset = () => {{ hero.pose({{}}); chest(hero, 0); xh.pose({{}}); chest(xh, 0); lungs(0); I.heart.scale.setScalar(1); xmat.uniforms.uCol.value.copy(CYAN); }};
  const kitchenRender = (focus, extra = {{}}) => E.render(K.scene, cam, {{ ...KLOOK, focus, ...extra }});
  const FACE = V3(0.1, 1.68, -0.6);

{''.join(shot_blocks)}

  return {{ shots: S, cues: CUES }};
}}
"""
    shots_js_path.write_text(shots_content, encoding='utf-8')
    print(f"Generated adaptive shots.js ({num_lines} shots).")

def run_cmd(cmd, cwd=None, env=None):
    print(f"\n[RUN] {cmd}")
    res = subprocess.run(cmd, shell=True, cwd=cwd, env=env, text=True, capture_output=True)
    if res.returncode != 0:
        print(f"STDERR: {res.stderr}")
        print(f"STDOUT: {res.stdout}")
        raise RuntimeError(f"Command failed with exit code {res.returncode}: {cmd}")
    print(res.stdout.strip())
    return res.stdout

def main():
    parser = argparse.ArgumentParser(description="Autonomous Cloud Runner for YouTube Shorts")
    parser.add_argument('--slot', default="auto", help="Slot ID (1-5 or auto)")
    parser.add_argument('--dry-run', action='store_true', help="Resolve slot and script without rendering/uploading")
    args = parser.parse_args()

    print("=" * 60)
    print(" 5-TIMES-DAILY AUTONOMOUS SHORTS PIPELINE")
    print("=" * 60)

    slots_cfg = load_slots_config()
    
    # Parse slot argument
    slot_choice = args.slot
    if not slot_choice or slot_choice.startswith('auto'):
        slot_id = detect_current_slot(slots_cfg)
        print(f"Auto-detected Slot: {slot_id} based on current UTC time.")
    else:
        # Support formats like '1', '1 - Geography & Flags'
        m = re.match(r'(\d+)', slot_choice)
        slot_id = m.group(1) if m else "1"

    slot_info = slots_cfg.get(slot_id, slots_cfg["1"])
    print(f"Slot {slot_id}: {slot_info['name']} (Scheduled: {slot_info['time_pkt']} PKT)")

    published = get_published_topics()
    print(f"Found {len(published)} previously published topics.")

    item = pick_topic_for_slot(slot_info, published)
    topic = item['topic']
    style = item.get('style', slot_info.get('style', 'deep-dive'))
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
        return

    # Scaffold project
    src_example = SKILL_DIR / 'styles' / style / 'example'
    if not src_example.exists():
        src_example = SKILL_DIR / 'styles' / 'deep-dive' / 'example'

    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    if proj_dir.exists():
        shutil.rmtree(proj_dir)
    shutil.copytree(src_example, proj_dir)

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

    # Generate adaptive shots
    write_adaptive_shots(proj_dir, title, item['lines'], style)

    py = sys.executable
    env = os.environ.copy()
    env['SOFTWARE_GL'] = '1'

    # 1. Synthesize Voice
    print("\n--- Synthesizing Calm Voiceover (Kokoro ONNX) ---")
    run_cmd(f'"{py}" "{SKILL_DIR}/scripts/voice.py" "{proj_dir}"', env=env)

    # 2. Whisper Word Alignment
    print("\n--- Subtitle Word Alignment (Faster-Whisper) ---")
    run_cmd(f'"{py}" "{SKILL_DIR}/scripts/words.py" "{proj_dir}"', env=env)

    # 3. Audio Cues & Calm Mixing
    print("\n--- Mixing Procedural Sound & Ambient Bed ---")
    run_cmd('node tools/capture.mjs cues', cwd=proj_dir, env=env)
    run_cmd(f'"{py}" tools/mix.py .', cwd=proj_dir, env=env)

    # 4. Render Video
    renders_dir = proj_dir / 'renders'
    renders_dir.mkdir(exist_ok=True)
    video_out = renders_dir / f"{slug}.mp4"
    print("\n--- Rendering 1080x1920 MP4 Video (Headless Chrome) ---")
    run_cmd(f'node tools/capture.mjs video "renders/{slug}.mp4"', cwd=proj_dir, env=env)

    if not video_out.exists():
        raise FileNotFoundError(f"Render failed, {video_out} not created")

    # 5. Upload to YouTube
    print("\n--- Uploading Short to YouTube ---")
    short_url = None
    try:
        from cloud.upload_youtube import upload_short
        desc = f"{item['lines'][0]['text']}\n\n#shorts #{slot_info['name'].replace(' ', '')} #curiosity"
        _, short_url = upload_short(
            video_path=video_out,
            title=title,
            description=desc,
            tags=tags,
            category_id=category_id,
            privacy_status="public"
        )
    except Exception as e:
        print(f"Direct YouTube upload failed or pending: {e}")
        short_url = f"[Manual/Pending Upload] {video_out.name}"

    # 6. Update _published.md
    today = datetime.now().strftime("%Y-%m-%d")
    log_line = f"| {today} | {topic} | {style} | {title} | {short_url} |\n"
    with open(PUBLISHED_FILE, 'a', encoding='utf-8') as f:
        f.write(log_line)

    print("\n" + "=" * 60)
    print(" 5-DAILY RUN COMPLETE!")
    print(f" Published: {title}")
    print(f" Genre: {slot_info['name']}")
    print(f" URL: {short_url}")
    print("=" * 60)

if __name__ == '__main__':
    main()
