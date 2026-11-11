#!/usr/bin/env python3
"""Master Autonomous Cloud Runner for GitHub Actions.
Executes the full pipeline without any human intervention:
1. Topic Discovery (Gemini API or curated viral queue)
2. Style Selection & Project Scaffolding
3. Script Writing (Calm collected tone, 0.88x speed, Whisper sync)
4. Three.js Video Rendering (Headless Chrome + Software GL)
5. YouTube Upload (YouTube Data API v3)
6. Appending to _published.md
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
            {"text": "This stretches your entire body into a thin, noodle-like strand, a process physicists call spaghettification.", "caps": "Stretching your *body | into a *noodle | *spaghettification"},
            {"text": "To an observer watching you from outside, time slows down completely.", "caps": "From the *outside | time slows *down | completely"},
            {"text": "They would see you freeze forever at the edge of the event horizon, slowly fading away.", "caps": "You *freeze | at the *edge | slowly *fading"},
            {"text": "But from your own perspective, you cross the horizon in seconds.", "caps": "From your *eyes | you cross the *edge | in *seconds"},
            {"text": "Inside, space and time swap roles, and all paths lead inevitably to the singularity.", "caps": "All *paths | lead to the *singularity"},
            {"text": "So if you ever drift through deep space, keep your distance, before you experience...", "caps": "Keep your *distance | before you *experience", "gap": 0.25}
        ]
    },
    {
        "topic": "What happens if you get rabies?",
        "style": "inside-out",
        "title": "What Actually Happens If You Get Rabies? #shorts",
        "sources": ["CDC, 'Rabies Virus Pathogenesis and Central Nervous System Infection'", "World Health Organization (WHO), 'Rabies Fact Sheet and Hydrophobia Clinical Data'"],
        "lines": [
            {"text": "What actually happens if an infected animal bites you?", "caps": "What *happens | if an infected *animal | *bites you?"},
            {"text": "The rabies virus enters your muscle tissue and travels silently up your nervous system.", "caps": "Virus travels *silently | up your *nerves"},
            {"text": "It can creep through your body for weeks or months without causing a single symptom.", "caps": "Creeping for *months | without any *symptoms"},
            {"text": "But the moment it reaches your brain, the survival rate drops to virtually zero.", "caps": "Once in your *brain | survival drops to *zero"},
            {"text": "It triggers intense brain inflammation, confusion, and terrifying spasms whenever you swallow.", "caps": "Severe *spasms | whenever you *swallow"},
            {"text": "This creates severe hydrophobia: a desperate fear of water.", "caps": "Creating intense | fear of *water"},
            {"text": "Fortunately, a prompt vaccine right after the bite stops the virus before it starts.", "caps": "A quick *vaccine | stops it *completely"},
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
        "style": "inside-out",
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
Write an original, calm, collected script (~90-100 words, calm explanation pace).
Format strictly as JSON with this schema:
{{
  "topic": "Short topic description",
  "style": "deep-dive", // or "inside-out", "stick-story", "dashcam-3d", "tall-tale"
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

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        raw_text = data['candidates'][0]['content']['parts'][0]['text']
        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    raise ValueError("Failed to parse Gemini response")

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

    # If all in list used, recycle with variation
    return CURATED_TOPICS[0]

def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')[:35]

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
