#!/usr/bin/env python3
"""Master Autonomous Cloud Runner for GitHub Actions.
Executes the full pipeline without any human intervention:
1. Topic Discovery (Gemini API or curated viral queue)
2. Style Selection & Project Scaffolding
3. Script Writing (Calm collected tone, 0.88x speed, Whisper sync)
4. Adaptive Three.js Shots generation (zero missing word errors)
5. Three.js Video Rendering (Headless Chrome + Software GL)
6. YouTube Upload (YouTube Data API v3)
7. Appending to _published.md
"""
import os
import re
import sys
import json
import time
import shutil
import urllib.request
import subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
PUBLISHED_FILE = ROOT / '_published.md'
SKILL_DIR = ROOT / 'faceless-shorts'
PROJECTS_DIR = ROOT / 'projects'

CURATED_TOPICS = [
    {
        "topic": "What happens if you fall into a black hole?",
        "style": "deep-dive",
        "title": "What Happens If You Fall In A Black Hole? #shorts",
        "sources": ["NASA Goddard, 'Black Holes: Gravitational Tidal Forces & Spaghettification'", "Astrophysical Journal, 'Event Horizon Crossing and Time Dilation'"],
        "lines": [
            {"text": "What actually happens if you fall into a black hole?", "caps": "What *happens | if you *fall | in a *black hole?"},
            {"text": "As you get closer, extreme gravity pulls much harder on your feet than your head.", "caps": "Gravity *pulls | harder on *feet | than your *head"},
            {"text": "This stretches your entire body into a thin strand, in a process physicists call spaghettification.", "caps": "Stretching your *body | into a *strand | *spaghettification"},
            {"text": "To an observer watching you from outside, time slows down completely.", "caps": "From the *outside | time slows *down | completely"},
            {"text": "They would see you freeze at the edge of the event horizon, slowly fading away.", "caps": "You *freeze | at the *edge | slowly *fading"},
            {"text": "From your own view, you cross the horizon in mere seconds.", "caps": "From your *eyes | you cross the *edge | in *seconds"},
            {"text": "Inside, space and time swap roles, and all paths lead inevitably to the singularity.", "caps": "All *paths | lead to the *singularity"},
            {"text": "So if you ever drift through deep space, keep your distance, before you experience...", "caps": "Keep your *distance | before you *experience", "gap": 0.25}
        ]
    },
    {
        "topic": "What happens if you get rabies?",
        "style": "deep-dive",
        "title": "What Actually Happens If You Get Rabies? #shorts",
        "sources": ["CDC, 'Rabies Virus Pathogenesis and Central Nervous System Infection'", "World Health Organization (WHO), 'Rabies Fact Sheet and Hydrophobia Clinical Data'"],
        "lines": [
            {"text": "What actually happens if an infected animal bites you?", "caps": "What *happens | if an infected *animal | *bites you?"},
            {"text": "The rabies virus enters your muscle tissue and travels silently up your nervous system.", "caps": "Virus travels *silently | up your *nerves"},
            {"text": "It can creep through your body for weeks or months without causing a single symptom.", "caps": "Creeping for *months | without any *symptoms"},
            {"text": "But the moment it reaches your brain, the survival rate drops to virtually zero.", "caps": "Once in your *brain | survival drops to *zero"},
            {"text": "It triggers intense brain inflammation, confusion, and terrifying spasms whenever you swallow.", "caps": "Severe *spasms | whenever you *swallow"},
            {"text": "This creates severe hydrophobia: a desperate fear of water.", "caps": "Creating intense | fear of *water"},
            {"text": "Fortunately, a prompt vaccine right after the bite stops the virus completely.", "caps": "A quick *vaccine | stops it *completely"},
            {"text": "So never delay a bite checkup, before you find out...", "caps": "Get *checked | before you *discover", "gap": 0.25}
        ]
    },
    {
        "topic": "What happens if you don't sleep for 11 days?",
        "style": "deep-dive",
        "title": "What Happens If You Stay Awake For 11 Days? #shorts",
        "sources": ["National Sleep Foundation, 'Randy Gardner Sleep Deprivation Record & Neurological Changes'", "Harvard Medical School, 'The Cumulative Effects of Total Sleep Loss'"],
        "lines": [
            {"text": "What actually happens if you refuse to sleep for 11 straight days?", "caps": "What *happens | if you don't *sleep | for *11 days?"},
            {"text": "After twenty-four hours, your reaction time slows as much as being legally drunk.", "caps": "After 24 *hours | brain acts legally *drunk"},
            {"text": "By day three, your brain starts suffering microsleeps, shutting off for seconds without your permission.", "caps": "By day *three | brain forces *microsleeps"},
            {"text": "By day five, vivid hallucinations begin, and your immune system drops drastically.", "caps": "Day *five | vivid *hallucinations | *begin"},
            {"text": "Toxic protein waste accumulates in brain cells because the brain only cleans itself during deep sleep.", "caps": "Toxic *waste | builds up in *brain cells"},
            {"text": "By day eleven, paranoia sets in and cognitive function collapses.", "caps": "Day *eleven | mental function *collapses"},
            {"text": "Surprisingly, a couple of long nights of sleep allows the brain to recover.", "caps": "Deep *rest | allows brain to *recover"},
            {"text": "So make sure you get to bed tonight, before you test...", "caps": "Get to *bed | before you *test", "gap": 0.25}
        ]
    },
    {
        "topic": "What happens if you drink ocean water?",
        "style": "deep-dive",
        "title": "Why You Should Never Drink Ocean Water #shorts",
        "sources": ["NOAA Ocean Service, 'Can Humans Drink Seawater?'", "Kidney International, 'Osmotic Dehydration and Renal Salt Excretion'"],
        "lines": [
            {"text": "Why should you never drink ocean water when stranded at sea?", "caps": "Why *never | drink ocean *water | at *sea?"},
            {"text": "Seawater has about four times more salt than your blood.", "caps": "Seawater has *4x | more *salt | than your *blood"},
            {"text": "When you drink it, salt floods your bloodstream and draws water directly out of your cells by osmosis.", "caps": "Salt draws *water | right out of *cells"},
            {"text": "Your cells shrink and shrivel, leaving you far more dehydrated than before.", "caps": "Your cells *shrink | leaving you more *dehydrated"},
            {"text": "To flush the extra salt out, your kidneys must produce more urine than the water you swallowed.", "caps": "Kidneys must *flush | more liquid than you *drank"},
            {"text": "This accelerates kidney failure and triggers rapid delirium.", "caps": "Leading to rapid | kidney *failure"},
            {"text": "Which is why drinking seawater actually speeds up dying of thirst.", "caps": "It speeds up *thirst | instead of *quenching it"},
            {"text": "So always collect rainwater instead, before you discover...", "caps": "Collect *rainwater | before you *discover", "gap": 0.25}
        ]
    }
]

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

def generate_with_gemini(api_key, published_topics):
    prompt = f"""You are an expert producer of viral YouTube Shorts in the style of Zack D. Films / Deep Dive 3D.
Previously published topics: {list(published_topics)}

Pick a completely fresh, unrepeated, viral curiosity topic in science, human body, space, survival, or weird history.
Write an original, calm, collected script (~80-100 words, calm explanation pace).
Format strictly as JSON with this schema:
{{
  "topic": "Short topic description",
  "style": "deep-dive",
  "title": "Short title under 60 chars ending in #shorts",
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
                    print(f"Successfully generated script using {model}!")
                    return res
        except Exception as e:
            print(f"Gemini model {model} attempt failed: {e}")
            continue

    raise ValueError("All Gemini model endpoints failed")

def pick_next_topic(published_topics):
    api_key = os.environ.get('GEMINI_API_KEY')
    if api_key:
        try:
            print("Querying Gemini API for a trending curiosity topic...")
            return generate_with_gemini(api_key, published_topics)
        except Exception as e:
            print(f"Gemini API generation failed ({e}), falling back to curated curriculum...")

    for item in CURATED_TOPICS:
        if item['topic'].lower() not in published_topics and item['title'].lower() not in published_topics:
            return item

    return CURATED_TOPICS[0]

def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')[:35]

def write_adaptive_shots(proj_dir, title, lines):
    """Generates a dynamic Three.js shots.js that perfectly maps to any number of lines without word-lookup errors."""
    shots_js_path = proj_dir / 'src' / 'shots.js'

    num_lines = len(lines)
    shot_blocks = []
    
    clean_title = title.replace('#shorts', '').strip()
    
    for i in range(num_lines):
        shot_id = f"S{i+1:02d}"
        if i == 0:
            # Hook shot
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
      pill('{clean_title.upper()[:24]}', 540, 340, eob(seg(lt, 0.15, 0.45)), '#FFD43B');
    }} }});
    cue(st, 'whoosh'); cue(st + 0.2, 'pop', {{ gain: 0.6 }}); }}"""
        elif i == num_lines - 1:
            # Outro shot
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
      pill('WHAT HAPPENS NEXT?', 540, 340, eob(seg(lt, 0.2, 0.45)), '#FFD43B');
    }} }});
    cue(st, 'whoosh'); cue(st + 0.25, 'slam', {{ gain: 0.7 }}); }}"""
        else:
            mode = i % 4
            if mode == 1:
                # X-ray lungs / chest shot
                block = f"""
  {{ const st = cut({i});
    add({{ id: '{shot_id}', at: st, note: 'X-ray: Body anatomy & internal effect', draw(lt, d, t, blit) {{
      reset();
      lungs(1 + Math.sin(lt * 3) * 0.05);
      chest(xh, 1);
      xh.pose({{ head: [4, -6, 0] }});
      cam.position.copy(lerpV(V3(0.55, 1.5, 1.6), V3(0.3, 1.42, 1.1), eio(lt / d)));
      cam.lookAt(0, 1.33, 0);
      E.render(X.scene, cam, {{ ...XLOOK, focus: cam.position.distanceTo(V3(0, 1.33, 0)) }});
      blit();
      pill('INTERNAL EFFECT', 540, 340, eob(seg(lt, 0.2, 0.45)), '#4FD1E8');
    }} }});
    cue(st, 'whoosh'); cue(st + 0.15, 'thud', {{ gain: 0.45 }}); }}"""
            elif mode == 2:
                # Macro vessel shot
                block = f"""
  {{ const st = cut({i});
    add({{ id: '{shot_id}', at: st, note: 'Macro: Cellular / vessel stream', draw(lt, d, t, blit) {{
      VS.update(t, -lt * 1.6, 0, 0);
      cam.position.set(0, 0, -lt * 1.6);
      cam.lookAt(0.15, -0.08, -lt * 1.6 - 5);
      E.render(VS.scene, cam, VLOOK);
      blit();
      pill('MICROSCOPIC VIEW', 540, 340, eob(seg(lt, 0.15, 0.4)), '#7CF29A');
    }} }});
    cue(st, 'whoosh'); cue(st + 0.2, 'pop', {{ gain: 0.5 }}); }}"""
            elif mode == 3:
                # X-ray Heart close-up
                block = f"""
  {{ const st = cut({i});
    add({{ id: '{shot_id}', at: st, note: 'X-ray: Heart rhythm pulse', draw(lt, d, t, blit) {{
      reset();
      const p = 0.5 + 0.5 * Math.sin(lt * 8);
      I.heart.scale.setScalar(1 + p * 0.15);
      I.heart.material.emissiveIntensity = 0.2 + p * 0.7;
      const H0 = V3(0.025, 1.41, 0.07);
      cam.position.copy(lerpV(V3(0.25, 1.48, 0.62), V3(0.12, 1.44, 0.42), eio(lt / d)));
      cam.lookAt(H0);
      E.render(X.scene, cam, {{ ...XLOOK, bloom: 0.6, focus: cam.position.distanceTo(H0) }});
      blit();
      pill('CRITICAL RESPONSE', 540, 340, eob(seg(lt, 0.2, 0.45)), '#FF8A8A');
    }} }});
    cue(st, 'whoosh'); cue(st + 0.2, 'heartbeat'); }}"""
            else:
                # Hero medium orbit
                block = f"""
  {{ const st = cut({i});
    add({{ id: '{shot_id}', at: st, note: 'Medium shot: Hero reaction', draw(lt, d, t, blit) {{
      reset();
      hero.pose({{ head: [2, -6 + Math.sin(lt * 2) * 3, 0], lid: -0.15, look: [6, 0] }});
      const a = lerp(0.55, 0.2, eio(lt / d));
      cam.position.set(0.1 + Math.sin(a) * 2.1, 1.45, -0.6 + Math.cos(a) * 2.1);
      cam.lookAt(0.1, 1.25, -0.6);
      kitchenRender(2.1);
      blit();
      pill('SURPRISING REALITY', 540, 340, eob(seg(lt, 0.2, 0.45)), '#C9D6DD');
    }} }});
    cue(st, 'whoosh'); cue(st + 0.2, 'pop', {{ gain: 0.5 }}); }}"""
        shot_blocks.append(block)

    shots_content = f"""// Auto-generated adaptive shots for: {title}
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
    print(f"Generated adaptive shots.js with {num_lines} dynamic shots.")

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
    print("=" * 60)
    print(" AUTONOMOUS CLOUD SHORT GENERATOR & PUBLISHER")
    print("=" * 60)

    published = get_published_topics()
    print(f"Found {len(published)} previously published topics.")

    item = pick_next_topic(published)
    topic = item['topic']
    style = item.get('style', 'deep-dive')
    title = item['title']
    slug = slugify(title.replace('#shorts', ''))
    proj_dir = PROJECTS_DIR / slug

    print(f"\nSelected Topic: {topic}")
    print(f"Style: {style}")
    print(f"Title: {title}")
    print(f"Project Folder: {proj_dir}")

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
        "sources": item.get('sources', ["Scientific Literature & Medical Records"]),
        "lines": item['lines']
    }
    (proj_dir / 'script.json').write_text(json.dumps(script_data, indent=2), encoding='utf-8')

    # Generate adaptive shots.js matching the exact lines
    write_adaptive_shots(proj_dir, title, item['lines'])

    # Python executable (venv or system)
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
        desc = f"{item['lines'][0]['text']}\n\n#shorts #science #whatif #curiosity"
        tags = ["shorts", "science", "what if", "facts", style]
        _, short_url = upload_short(
            video_path=video_out,
            title=title,
            description=desc,
            tags=tags,
            category_id="28",
            privacy_status="public"
        )
    except Exception as e:
        print(f"Direct YouTube upload failed or not configured: {e}")
        short_url = f"[Manual/Pending Upload] {video_out.name}"

    # 6. Update _published.md
    today = datetime.now().strftime("%Y-%m-%d")
    log_line = f"| {today} | {topic} | {style} | {title} | {short_url} |\n"
    with open(PUBLISHED_FILE, 'a', encoding='utf-8') as f:
        f.write(log_line)

    print("\n" + "=" * 60)
    print(" RUN COMPLETE!")
    print(f" Published: {title}")
    print(f" URL: {short_url}")
    print("=" * 60)

if __name__ == '__main__':
    main()
