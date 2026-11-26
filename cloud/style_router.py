#!/usr/bin/env python3
"""Fast Multi-Style 2D Orchestrator (visual_engine_2d + Paper Atlas + Stick Story).

Routes each topic cleanly to the best CPU-fast 2D Canvas visual engine:
  - `2d-motion`   : Infographic / cosmic / physics procedural vectors (COSMIC_SPACE, ATOMIC_PHYSICS, alternation)
  - `paper-atlas` : Cut-paper parchment maps, timelines, seals & period figures (HISTORIC_DOCUMENTARY)
  - `stick-story` : Acting stick-figure characters, step cards, day/night & outdoor hazard sets (SURVIVAL_TACTICAL)

All three styles share:
  - Bright frame-0 hook + 0s seamless loop (zero black fade-in / fade-out in main.js)
  - Mid-line visual sub-cuts via Wd() for a 2-3.4s visual cut rhythm at calm 0.91x speech
  - Topic-specific, zero-boilerplate labels audited by AssetGuard
  - Fresh per-video tools/mix.py audio + tools/capture.mjs Chrome driver
"""
from __future__ import annotations

import re
import json
import math
import shutil
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

from cloud.asset_guard import (
    check_boilerplate_cards,
    compute_asset_seed,
    compute_text_sha256,
    normalize_card_text,
)
from cloud.visual_engine_2d import (
    SKILL_DIR,
    detect_topic_theme,
    pick_variation_palette,
    build_music_config,
    generate_mix_py,
    scaffold_2d_project,
    _clean_short_phrase,
    _extract_focus_word,
    _extract_line_pill,
    _extract_stat_from_line,
    _extract_pipeline_stages,
    _select_sfx_cue,
)

SUPPORTED_2D_STYLES = ("2d-motion", "paper-atlas", "stick-story")


def select_visual_style(
    topic: str,
    lines: List[Dict],
    theme_name: str,
    recent_assets: Optional[List[Dict[str, Any]]] = None,
    requested_style: str = "",
    variant_offset: int = 0,
) -> str:
    """Chooses the best fast-2D visual style while avoiding consecutive same-style stagnation."""
    recent_assets = recent_assets or []
    last_style = recent_assets[-1].get("style", "") if recent_assets else ""

    if requested_style in SUPPORTED_2D_STYLES:
        if requested_style == last_style and variant_offset > 0:
            return "2d-motion" if requested_style != "2d-motion" else "stick-story"
        return requested_style

    if theme_name == "HISTORIC_DOCUMENTARY":
        if last_style == "paper-atlas" or (variant_offset % 2 == 1):
            return "2d-motion"
        return "paper-atlas"

    if theme_name == "SURVIVAL_TACTICAL":
        if last_style == "stick-story" or (variant_offset % 2 == 1):
            return "2d-motion"
        return "stick-story"

    return "2d-motion"


def _copy_shared_tools_and_core(proj_dir: Path, style_dir: Path, music_cfg: Dict[str, Any]) -> Tuple[str, str]:
    """Copies fonts, lib.js, timing.js, captions.js, kit.js, capture.mjs and writes fresh mix.py."""
    fonts_dir = proj_dir / "fonts"
    fonts_dir.mkdir(parents=True, exist_ok=True)
    src_fonts = style_dir / "fonts"
    if src_fonts.exists():
        for font_file in src_fonts.iterdir():
            if font_file.is_file():
                shutil.copy2(font_file, fonts_dir / font_file.name)

    tools_dir = proj_dir / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    # Use inside-out capture.mjs if present (universal OP driver)
    cap_src = SKILL_DIR / "styles" / "inside-out" / "example" / "tools" / "capture.mjs"
    if not cap_src.exists():
        cap_src = style_dir / "tools" / "capture.mjs"
    if cap_src.exists():
        shutil.copy2(cap_src, tools_dir / "capture.mjs")

    mix_code = generate_mix_py(music_cfg)
    (tools_dir / "mix.py").write_text(mix_code, encoding="utf-8", newline="\n")

    src_dir = proj_dir / "src"
    core_dir = src_dir / "core"
    core_dir.mkdir(parents=True, exist_ok=True)
    for core_name in ["lib.js", "timing.js", "captions.js", "kit.js"]:
        csrc = style_dir / "src" / "core" / core_name
        if csrc.exists():
            shutil.copy2(csrc, core_dir / core_name)

    kit_code = (core_dir / "kit.js").read_text(encoding="utf-8") if (core_dir / "kit.js").exists() else ""
    return mix_code, kit_code


def _build_no_fade_main_js(extra_fonts: List[str], initial_bg: str = "#111111") -> str:
    """Writes window.OP-compatible main.js with instant bright frame-0 hook and 0s loop seam (no black fade)."""
    font_loads = " ".join(f"await document.fonts.load('{f}');" for f in extra_fonts)
    return f"""// Auto-generated Multi-Style 2D Main Boot (Bright Frame-0 + Zero-Fade Loop Seam)
import {{ W, H, setCtx, ctx, clamp, eo, eio }} from './core/lib.js';
import {{ T, loadTiming }} from './core/timing.js';
import {{ buildCaptions, drawCaption, captionList }} from './core/captions.js';
import {{ buildShots }} from './shots.js';

const cv = document.getElementById('cv');
setCtx(cv.getContext('2d'));
const OP = (window.OP = {{ ready: false }});

function draw(t) {{
  t = clamp(t, 0, T.dur - 1e-4);
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.letterSpacing = '0px';
  ctx.fillStyle = '{initial_bg}'; ctx.fillRect(0, 0, W, H);
  const S = OP._shots; let i = S.length - 1; while (i > 0 && S[i].at > t) i--;
  const sh = S[i], end = i < S.length - 1 ? S[i + 1].at : T.dur, d = Math.max(0.05, end - sh.at), lt = t - sh.at;
  const punch = 1 + 0.055 * (1 - eo(clamp(lt / 0.22)));
  const drift = 1 + (sh.zoom ?? 0.06) * eio(clamp(lt / d));
  const [cx, cy] = sh.cam || [540, 860];
  ctx.save(); ctx.translate(cx, cy); ctx.scale(punch * drift, punch * drift); ctx.translate(-cx, -cy);
  sh.draw(lt, d, t);
  ctx.restore();
  ctx.globalAlpha = 1; ctx.letterSpacing = '0px';
  if (i > 0 && lt < 0.09) {{ ctx.fillStyle = '#FFFFFF'; ctx.globalAlpha = 0.35 * (1 - lt / 0.09); ctx.fillRect(0, 0, W, H); ctx.globalAlpha = 1; }}
  drawCaption(t);
}}

(async () => {{
  try {{
    {font_loads}
    const script = await (await fetch('script.json', {{ cache: 'no-store' }})).json();
    await loadTiming();
    buildCaptions(script);
    const {{ shots, cues }} = buildShots();
    shots.sort((a, b) => a.at - b.at);
    OP._shots = shots; OP.script = script;
    OP.duration = () => T.dur;
    OP.draw = draw;
    OP.frame = (t, q = 0.92) => {{ draw(t); return cv.toDataURL('image/jpeg', q); }};
    OP.shots = () => shots.map((s, i) => ({{ id: s.id, at: +s.at.toFixed(3), end: +(i < shots.length - 1 ? shots[i + 1].at : T.dur).toFixed(3), note: s.note || '' }}));
    OP.captions = () => captionList().map((c) => ({{ s: +c.s.toFixed(3), e: +c.e.toFixed(3), text: c.words.map((w) => (w.hi ? '*' : '') + w.txt).join(' ') }}));
    OP.cues = () => cues.slice().sort((a, b) => a.t - b.t);
    OP.ready = true;
    const q = new URLSearchParams(location.search);
    if (!q.has('capture')) {{
      if (q.has('t')) draw(+q.get('t'));
      else {{
        const audio = new Audio('data/mix.wav'); let t0 = null;
        const btn = document.getElementById('play'); btn.hidden = false;
        btn.onclick = () => {{ btn.hidden = true; t0 = performance.now(); audio.currentTime = 0; audio.play().catch(() => {{}}); }};
        const loop = (now) => {{ const t = t0 == null ? 0 : (now - t0) / 1000; draw(t0 == null ? 0 : t); if (t0 != null && t > T.dur) {{ t0 = null; btn.hidden = false; }} requestAnimationFrame(loop); }};
        requestAnimationFrame(loop);
      }}
    }}
  }} catch (e) {{ OP.bootError = String(e && e.stack || e); console.error(e); }}
}})();
"""


def _extract_years(text: str) -> List[str]:
    yrs = re.findall(r'\b(1[0-9]{3}|20[0-2][0-9])\b', text)
    return list(dict.fromkeys(yrs))


def _needs_subcut(line: Dict[str, Any]) -> bool:
    txt = str(line.get("text", "")).strip()
    words = txt.split()
    return len(words) >= 11


def _scaffold_paper_atlas(
    proj_dir: Path,
    title: str,
    topic: str,
    lines: List[Dict],
    theme_name: str,
    seed: str,
    music_cfg: Dict[str, Any],
    run_id: str,
) -> Tuple[str, str, List[str]]:
    """Builds a cut-paper historical short using the Paper Atlas engine."""
    style_dir = SKILL_DIR / "styles" / "paper-atlas" / "example"
    mix_code, kit_code = _copy_shared_tools_and_core(proj_dir, style_dir, music_cfg)

    clean_title = re.sub(r'#shorts', '', title, flags=re.IGNORECASE).strip()
    topic_anchor = _clean_short_phrase(clean_title or topic, 18)
    full_text = f"{topic} {clean_title} " + " ".join(l.get("text", "") for l in lines)
    years = _extract_years(full_text)
    hero_year = years[0] if years else "ARCHIVE"
    is_maritime = any(k in full_text.lower() for k in ("ship", "harbor", "sea", "port", "molasses", "halifax", "flood", "wave", "lake", "ocean", "snails", "purple"))
    is_hall = any(k in full_text.lower() for k in ("king", "emperor", "queen", "roman", "qin", "council", "palace", "pyramid", "flags"))

    seed_int = int(hashlib.sha256((seed or topic).encode("utf-8")).hexdigest()[:8], 16)
    used_pills: set = set()
    card_texts: List[str] = []
    scene_sequence: List[str] = []
    shot_blocks: List[str] = []
    has_subcuts = False

    timeline_years = years[:3] if len(years) >= 3 else _extract_pipeline_stages(lines, topic_anchor)
    roles = ["scholar", "merchant", "sailor", "guard", "worker", "king"]

    for i, ln in enumerate(lines):
        lt_txt = str(ln.get("text", ""))
        custom_vis = ln.get("visual") if isinstance(ln.get("visual"), dict) else None
        focus_word = (custom_vis.get("focus_word") if custom_vis else None) or _extract_focus_word(ln)

        pill = ""
        if custom_vis and custom_vis.get("pill"):
            cand = _clean_short_phrase(custom_vis["pill"], 18)
            ok, _ = check_boilerplate_cards([cand], topic=topic, title=clean_title, script_text=lt_txt)
            if ok and normalize_card_text(cand) not in used_pills:
                pill = cand
                used_pills.add(normalize_card_text(cand))
        if not pill:
            pill = _clean_short_phrase(_extract_line_pill(ln, used_pills, topic_anchor), 18)

        val_str, lbl_str = _extract_stat_from_line(lt_txt, topic_anchor)
        slip_txt = _clean_short_phrase(val_str if any(c.isdigit() for c in val_str) else pill, 16)
        role = roles[(seed_int + i) % len(roles)]
        line_yrs = _extract_years(lt_txt)
        ribbon_txt = _clean_short_phrase(line_yrs[0] if line_yrs else (hero_year if i == 0 else pill), 12)
        sfx = _select_sfx_cue(lt_txt, "PAPER_ATLAS", i == 0, i == len(lines) - 1)
        do_subcut = (0 < i < len(lines) - 1) and _needs_subcut(ln)

        # Pick scene archetype deterministically with non-repeating neighbors
        modes = ["PAPER_MAP_ROUTE", "PAPER_HARBOR" if is_maritime else "PAPER_HALL", "PAPER_FIGURE_STAGE", "PAPER_TIMELINE"]
        mode = modes[0] if i == 0 else ("PAPER_LOOP_SEAL" if i == len(lines) - 1 else modes[(i + (seed_int % 2)) % len(modes)])
        if scene_sequence and mode == scene_sequence[-1]:
            mode = modes[(modes.index(mode) + 1) % len(modes)]
        scene_sequence.append(mode)

        pill_js = json.dumps(pill)
        slip_js = json.dumps(slip_txt)
        ribbon_js = json.dumps(ribbon_txt)
        focus_js = json.dumps(focus_word)
        anchor_js = json.dumps(topic_anchor)
        tl_js = json.dumps([_clean_short_phrase(str(x), 8) or str(x)[:8] for x in timeline_years])
        sfx_js = json.dumps(sfx)
        initial_letter = json.dumps((clean_title[:1] or "H").upper())

        def _draw_bg(m_name: str, step_idx: int) -> str:
            if m_name == "PAPER_MAP_ROUTE":
                return f"K.map({{ seed: {seed_int % 97 + step_idx}, highlight: {step_idx % 3}, route: eo(seg(lt, 0.08, Math.max(0.4, d * 0.85))), labels: [[{ribbon_js}, 330, 560], [{pill_js}, 730, 1020]] }});"
            elif m_name == "PAPER_HARBOR":
                return f"K.harbor(t * 0.9, 520 + Math.sin(lt * 1.1) * 90); K.figure({{ x: 240, y: 1260, h: 460, role: '{role}', arm: 25 * Math.sin(lt * 2.5) }});"
            elif m_name == "PAPER_HALL":
                return f"K.hall(); K.figure({{ x: 540, y: 1360, h: 560, role: '{role}', walk: lt * 2.2, arm: 20 }});"
            elif m_name == "PAPER_TIMELINE":
                tl_prog = min(1.0, (step_idx + 0.5) / max(1, len(lines) - 1))
                return f"K.parchment({seed_int % 53 + step_idx}); K.map({{ seed: {step_idx + 5}, highlight: {step_idx % 2}, route: 0.65, labels: [[{pill_js}, 420, 620]] }}); K.timeline({tl_js}, 230, 1180, 620, eo(seg(lt, 0.1, 0.8)) * {tl_prog:.2f}, {min(len(timeline_years)-1, step_idx % 3)});"
            elif m_name == "PAPER_FIGURE_STAGE":
                return f"K.parchment({seed_int % 31 + step_idx}); K.hall(); K.figure({{ x: 350, y: 1350, h: 520, role: '{role}', arm: 35 * eo(seg(lt, 0.15, 0.5)) }});"
            else:
                return f"K.parchment({seed_int % 41 + 9}); K.map({{ seed: 7, highlight: 1, route: 1, labels: [[{anchor_js}, 520, 640]] }}); K.seal(820, 1060, eob(seg(lt, 0.12, 0.42)), {initial_letter});"

        card_texts.extend([pill, slip_txt, ribbon_txt])
        if do_subcut:
            has_subcuts = True
            sub_mode = modes[(modes.index(mode) + 1) % len(modes)]
            scene_sequence.append(sub_mode)
            draw_a = _draw_bg(mode, i)
            draw_b = _draw_bg(sub_mode, i + 10)
            block = f"""
  {{ const st = cut({i});
    const fw = {focus_js};
    const rawSplit = fw ? Wd(fw, {i}) - 0.08 : st + 2.0;
    const nextSt = ({i} + 1 < T.lines.length) ? cut({i} + 1) : T.dur;
    const splitAt = (rawSplit > st + 1.4 && rawSplit < nextSt - 1.0) ? rawSplit : (st + (nextSt - st) * 0.52);
    add({{ id: 'S{i+1:02d}a', at: st, cam: [540, 820], zoom: 0.05, note: 'Paper Atlas beat A', draw(lt, d, t) {{
      {draw_a}
      K.ribbon({ribbon_js}, 540, 260, eob(seg(lt, 0.02, 0.3)), 64);
    }} }});
    add({{ id: 'S{i+1:02d}b', at: splitAt, cam: [520, 760], zoom: 0.07, note: 'Paper Atlas beat B (sub-cut)', draw(lt, d, t) {{
      {draw_b}
      K.slip({slip_js}, 540, 1040, eob(seg(lt, 0.02, 0.26)), -0.02, 48);
    }} }});
    cue(st, 'whoosh', {{ gain: 0.45 }}); cue(splitAt, 'pop', {{ gain: 0.5 }}); cue(splitAt + 0.12, {sfx_js}, {{ gain: 0.55 }}); }}"""
        else:
            draw_main = _draw_bg(mode, i)
            if i == 0:
                top_call = f"K.ribbon({ribbon_js}, 540, 260, 0.88 + 0.12 * eob(seg(lt, 0, 0.24)), 66);"
                bot_call = f"K.slip({slip_js}, 540, 1140, 0.88 + 0.12 * eob(seg(lt, 0, 0.28)), 0.02, 44);"
            else:
                top_call = f"K.slip({pill_js}, 540, 250, eob(seg(lt, 0.02, 0.28)), -0.02, 46);"
                bot_call = f"K.slip({slip_js}, 540, 1140, lt > hit ? eob(seg(lt, hit, hit + 0.25)) : eob(seg(lt, 0.12, 0.4)), 0.02, 44);"
            block = f"""
  {{ const st = cut({i});
    const fw = {focus_js};
    const hit = fw ? Math.max(0.15, Wd(fw, {i}) - st) : 0.3;
    add({{ id: 'S{i+1:02d}', at: st, cam: [540, 820], zoom: 0.06, note: 'Paper Atlas stage', draw(lt, d, t) {{
      {draw_main}
      {top_call}
      {bot_call}
    }} }});
    {"cue(st + hit, " + sfx_js + ", { gain: 0.55 });" if i == 0 else "cue(st, 'whoosh', { gain: 0.45 }); cue(st + hit, " + sfx_js + ", { gain: 0.55 });"} }}"""
        shot_blocks.append(block)

    shots_body = "\n".join(shot_blocks)
    shots_code = f"""// Auto-generated Paper Atlas Shots (Zero Blackout, Mid-Line Sub-Cuts, Wd() Sync)
import {{ ctx, W, H, clamp, lerp, seg, eo, eio, eob, rnd }} from './core/lib.js';
import {{ L, Le, Wd, T }} from './core/timing.js';
import * as K from './core/kit.js';

export function buildShots() {{
  const S = [], CUES = [];
  const add = (o) => (S.push(o), o);
  const cue = (t, type, o = {{}}) => CUES.push({{ t: +t.toFixed(3), type, ...o }});
  const cut = (i) => (i === 0 ? 0 : L(i) - 0.08);
{shots_body}
  return {{ shots: S, cues: CUES }};
}}
"""
    (proj_dir / "src" / "shots.js").write_text(shots_code, encoding="utf-8", newline="\n")
    main_code = _build_no_fade_main_js(["900 100px Inter", "700 100px Caladea"], initial_bg="#E9DCBC")
    (proj_dir / "src" / "main.js").write_text(main_code, encoding="utf-8", newline="\n")

    safe_title_html = json.dumps(title)[1:-1].replace("<", "&lt;").replace(">", "&gt;")
    html_code = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{safe_title_html}</title>
<style>
@font-face {{ font-family: 'Inter'; font-weight: 900; src: url('fonts/Inter-Black.otf'); }}
@font-face {{ font-family: 'Caladea'; font-weight: 700; src: url('fonts/Caladea-Bold.ttf'); }}
html, body {{ margin: 0; background: #E9DCBC; height: 100%; }} body {{ display: flex; align-items: center; justify-content: center; }}
canvas {{ display: block; height: 100vh; width: auto; max-width: 100vw; object-fit: contain; }} body.capture canvas {{ height: auto; }}
#play {{ position: fixed; font: 900 28px Inter, sans-serif; padding: 18px 36px; border: 0; border-radius: 40px; background: #C8952F; cursor: pointer; }}
</style></head>
<body><canvas id="cv" width="1080" height="1920"></canvas><button id="play" hidden>▶ PLAY</button>
<script>if (location.search.includes('capture')) document.body.className = 'capture';</script>
<script type="module" src="src/main.js"></script></body></html>
"""
    (proj_dir / "index.html").write_text(html_code, encoding="utf-8", newline="\n")

    unique_cards = list(dict.fromkeys(c for c in card_texts if c))
    manifest = {
        "run_id": str(run_id),
        "asset_seed": seed,
        "project_dir_name": proj_dir.name,
        "title": title,
        "topic": topic,
        "theme": theme_name,
        "style": "paper-atlas",
        "palette_id": "paper_atlas_parchment",
        "focal_vector": "PAPER_ATLAS",
        "has_subcuts": has_subcuts,
        "scene_sequence": scene_sequence,
        "background_sequence": ["PARCHMENT"] * len(scene_sequence),
        "card_texts": unique_cards,
        "music_config": music_cfg,
        "shots_sha256": compute_text_sha256(shots_code),
        "file_hashes": {
            "src/core/kit.js": compute_text_sha256(kit_code),
            "src/shots.js": compute_text_sha256(shots_code),
            "src/main.js": compute_text_sha256(main_code),
            "tools/mix.py": compute_text_sha256(mix_code),
            "index.html": compute_text_sha256(html_code),
        },
    }
    (proj_dir / "asset_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    return theme_name, "paper_atlas_parchment", scene_sequence


def _scaffold_stick_story(
    proj_dir: Path,
    title: str,
    topic: str,
    lines: List[Dict],
    theme_name: str,
    seed: str,
    music_cfg: Dict[str, Any],
    run_id: str,
) -> Tuple[str, str, List[str]]:
    """Builds a dynamic acting Stick Story short (outdoor + indoor day/night sets + gold step cards)."""
    style_dir = SKILL_DIR / "styles" / "stick-story" / "example"
    mix_code, kit_code = _copy_shared_tools_and_core(proj_dir, style_dir, music_cfg)

    clean_title = re.sub(r'#shorts', '', title, flags=re.IGNORECASE).strip()
    topic_anchor = _clean_short_phrase(clean_title or topic, 16)
    full_text = f"{topic} {clean_title} " + " ".join(l.get("text", "") for l in lines).lower()
    is_outdoor = any(k in full_text for k in ("avalanche", "snow", "silo", "grain", "water", "ocean", "rip", "lightning", "flood", "canyon", "desert", "car", "crowd"))
    is_grain_or_sand = any(k in full_text for k in ("grain", "silo", "corn", "kernels", "quicksand", "sand", "snow", "avalanche"))
    is_snow = any(k in full_text for k in ("snow", "avalanche"))
    is_water = (not is_grain_or_sand) and any(k in full_text for k in ("water", "ocean", "rip", "car", "flood", "canyon", "wave", "lake", "river"))

    seed_int = int(hashlib.sha256((seed or topic).encode("utf-8")).hexdigest()[:8], 16)
    used_pills: set = set()
    card_texts: List[str] = []
    scene_sequence: List[str] = []
    shot_blocks: List[str] = []
    has_subcuts = False

    step_num = 1
    danger_words = (
        "never", "don't", "myth", "kill", "kills", "fatal", "trap", "fail", "fails",
        "tear", "crush", "crushing", "drown", "panic", "locking", "tightens", "buried",
        "burial", "deadly", "snap", "collapse", "suffocat", "hazard", "risk", "burst"
    )
    safe_words = ("create", "pocket", "swim", "parallel", "float", "relax", "wait", "survive", "escape", "rescue", "safe", "breathe slowly")

    for i, ln in enumerate(lines):
        lt_txt = str(ln.get("text", ""))
        custom_vis = ln.get("visual") if isinstance(ln.get("visual"), dict) else None
        focus_word = (custom_vis.get("focus_word") if custom_vis else None) or _extract_focus_word(ln)

        pill = ""
        if custom_vis and custom_vis.get("pill"):
            cand = _clean_short_phrase(custom_vis["pill"], 14)
            ok, _ = check_boilerplate_cards([cand], topic=topic, title=clean_title, script_text=lt_txt)
            if ok and normalize_card_text(cand) not in used_pills:
                pill = cand
                used_pills.add(normalize_card_text(cand))
        if not pill:
            pill = _clean_short_phrase(_extract_line_pill(ln, used_pills, topic_anchor), 14)

        val_str, lbl_str = _extract_stat_from_line(lt_txt, topic_anchor)
        step_lbl = _clean_short_phrase(pill, 13)
        stat_pill = _clean_short_phrase(val_str if any(c.isdigit() for c in val_str) else lbl_str, 18)
        sfx = _select_sfx_cue(lt_txt, "STICK_STORY", i == 0, i == len(lines) - 1)
        do_subcut = (0 < i < len(lines) - 1) and _needs_subcut(ln)

        is_night = (0 < i < len(lines) - 1) and (i % 2 == 1)
        is_danger = any(w in lt_txt.lower() for w in danger_words)
        is_safe = (not is_danger) and any(w in lt_txt.lower() for w in safe_words)
        mood = "happy" if i == len(lines) - 1 else ("scared" if is_danger else ("worried" if i == 0 else "determined"))

        stages = ["STICK_OUTDOOR" if is_outdoor else "STICK_ROOM", "STICK_CLOSEUP", "STICK_STEP", "STICK_HAZARD"]
        mode = stages[0] if i == 0 else ("STICK_SAFE_OUTRO" if i == len(lines) - 1 else stages[(i + (seed_int % 2)) % len(stages)])
        if scene_sequence and mode == scene_sequence[-1]:
            mode = stages[(stages.index(mode) + 1) % len(stages)]
        scene_sequence.append(mode)

        step_js = json.dumps(step_lbl)
        stat_js = json.dumps(stat_pill)
        focus_js = json.dumps(focus_word)
        sfx_js = json.dumps(sfx)
        is_night_js = "true" if is_night else "false"

        def _render_stage(m_name: str, cur_step: int) -> str:
            if m_name == "STICK_OUTDOOR":
                bg_fn = "drawGrainStage" if is_grain_or_sand else ("drawWaterStage" if is_water else "drawFieldStage")
                pill_sc = "0.88 + 0.12 * eob(seg(lt, 0, 0.25))" if i == 0 else "eob(seg(lt, 0.05, 0.35))"
                return (
                    f"{bg_fn}(t, {is_night_js}); "
                    f"K.person({{ x: 520, y: 1500, h: 760, dir: 1, walk: lt * 2.0, mood: '{mood}', glow: {is_night_js} }}); "
                    f"K.counterPill({stat_js}, 540, 220, {pill_sc});"
                )
            elif m_name == "STICK_ROOM":
                room = "kitchen" if (seed_int + i) % 3 == 1 else ("hallway" if (seed_int + i) % 3 == 2 else "livingRoom")
                pill_sc = "0.88 + 0.12 * eob(seg(lt, 0, 0.25))" if i == 0 else "eob(seg(lt, 0.05, 0.35))"
                return (
                    f"K.{room}({{ night: {is_night_js} }}); "
                    f"K.person({{ x: 540, y: 1520, h: 780, dir: -1, mood: '{mood}', glow: {is_night_js}, arms: {{ L: [-25, 20], R: [45, -35] }} }}); "
                    f"K.counterPill({stat_js}, 540, 220, {pill_sc});"
                )
            elif m_name == "STICK_CLOSEUP":
                return (
                    f"K.livingRoom({{ night: {is_night_js} }}); "
                    f"K.bigHead(540, 880, 290, {{ mood: '{mood}', look: [Math.sin(lt * 2) * 0.4, 0] }}); "
                    f"K.counterPill({step_js}, 540, 240, eob(seg(lt, 0.05, 0.32)));"
                )
            elif m_name == "STICK_STEP":
                bg_stmt = f"drawFieldStage(t, {is_night_js});" if is_outdoor else f"K.hallway({{ night: {is_night_js} }});"
                return (
                    f"{bg_stmt} "
                    f"K.person({{ x: 460, y: 1510, h: 740, dir: 1, mood: 'determined', glow: {is_night_js}, arms: {{ L: [-15, 20], R: [70, -25] }} }}); "
                    f"K.stepCard({cur_step}, {step_js}, 540, 290, eob(seg(lt, 0.08, 0.38)));"
                )
            elif m_name == "STICK_HAZARD":
                mark = "K.cross(760, 720, eob(seg(lt, 0.12, 0.38)) * 1.4);" if is_danger else ("K.check(760, 720, eob(seg(lt, 0.12, 0.38)) * 1.4);" if is_safe else f"K.counterPill({stat_js}, 750, 720, eob(seg(lt, 0.12, 0.38)));")
                bg_stmt = f"drawGrainStage(t, {is_night_js});" if is_grain_or_sand else (f"drawWaterStage(t, {is_night_js});" if is_water else (f"drawFieldStage(t, {is_night_js});" if is_outdoor else f"K.livingRoom({{ night: {is_night_js} }});"))
                return (
                    f"{bg_stmt} "
                    f"K.person({{ x: 380, y: 1510, h: 750, dir: 1, mood: '{mood}', glow: {is_night_js}, lean: -8 }}); "
                    f"{mark} K.counterPill({step_js}, 540, 230, eob(seg(lt, 0.05, 0.35)));"
                )
            else:
                bg_stmt = "drawGrainStage(t, false);" if is_grain_or_sand else ("drawWaterStage(t, false);" if is_water else ("drawFieldStage(t, false);" if is_outdoor else "K.livingRoom({ night: false });"))
                badge = "K.check(820, 760, eob(seg(lt, 0.15, 0.4))); " if is_safe else "K.cross(820, 760, eob(seg(lt, 0.15, 0.4))); "
                end_mood = "happy" if is_safe else "worried"
                return (
                    f"{bg_stmt} "
                    f"K.person({{ x: 520, y: 1510, h: 770, dir: 1, mood: '{end_mood}', glow: false, arms: {{ L: [-40, -20], R: [85, -35] }} }}); "
                    f"{badge}"
                    f"K.counterPill({stat_js}, 540, 230, eob(seg(lt, 0.05, 0.35)));"
                )

        cur_step_val = step_num
        if mode == "STICK_STEP":
            step_num += 1
        card_texts.extend([step_lbl, stat_pill])

        if do_subcut:
            has_subcuts = True
            sub_mode = "STICK_HAZARD" if mode != "STICK_HAZARD" else "STICK_CLOSEUP"
            scene_sequence.append(sub_mode)
            draw_a = _render_stage(mode, cur_step_val)
            draw_b = _render_stage(sub_mode, cur_step_val)
            block = f"""
  {{ const st = cut({i});
    const fw = {focus_js};
    const rawSplit = fw ? Wd(fw, {i}) - 0.08 : st + 2.0;
    const nextSt = ({i} + 1 < T.lines.length) ? cut({i} + 1) : T.dur;
    const splitAt = (rawSplit > st + 1.4 && rawSplit < nextSt - 1.0) ? rawSplit : (st + (nextSt - st) * 0.52);
    add({{ id: 'S{i+1:02d}a', at: st, cam: [540, 860], zoom: 0.06, note: 'Stick Story beat A', draw(lt, d, t) {{ {draw_a} }} }});
    add({{ id: 'S{i+1:02d}b', at: splitAt, cam: [540, 780], zoom: 0.07, note: 'Stick Story beat B (sub-cut)', draw(lt, d, t) {{ {draw_b} }} }});
    cue(st, 'whoosh', {{ gain: 0.45 }}); cue(splitAt, 'pop', {{ gain: 0.55 }}); cue(splitAt + 0.12, {sfx_js}, {{ gain: 0.55 }}); }}"""
        else:
            draw_single = _render_stage(mode, cur_step_val)
            block = f"""
  {{ const st = cut({i});
    const fw = {focus_js};
    const hit = fw ? Math.max(0.15, Wd(fw, {i}) - st) : 0.3;
    add({{ id: 'S{i+1:02d}', at: st, cam: [540, 860], zoom: 0.06, note: 'Stick Story stage', draw(lt, d, t) {{ {draw_single} }} }});
    {"cue(st + hit, " + sfx_js + ", { gain: 0.55 });" if i == 0 else "cue(st, 'whoosh', { gain: 0.45 }); cue(st + hit, " + sfx_js + ", { gain: 0.55 });"} }}"""
        shot_blocks.append(block)

    shots_body = "\n".join(shot_blocks)
    shots_code = f"""// Auto-generated Stick Story Shots (Day/Night & Outdoor Hazard Stage + Wd() Sub-Cuts)
import {{ ctx, W, H, clamp, lerp, seg, eo, eio, eob, rnd, rr, circle }} from './core/lib.js';
import {{ L, Le, Wd, T }} from './core/timing.js';
import * as K from './core/kit.js';

function drawFieldStage(t, night) {{
  ctx.fillStyle = night ? K.P.nSky : K.P.sky; ctx.fillRect(-300, -300, W + 600, 1400);
  circle(840, 420, 68, night ? '#F4EBC8' : '#FFE082');
  ctx.fillStyle = night ? K.P.nFloor : K.P.floor; ctx.fillRect(-300, 1180, W + 600, H - 1180 + 300);
  ctx.fillStyle = night ? K.P.nFloorDark : K.P.floorDark; ctx.fillRect(-300, 1180, W + 600, 32);
}}

function drawWaterStage(t, night) {{
  drawFieldStage(t, night);
  ctx.fillStyle = night ? '#1E3F5A' : '#4C9ED9';
  ctx.beginPath(); ctx.moveTo(-300, 1920);
  for (let x = -300; x <= W + 300; x += 60) ctx.lineTo(x, 1260 + Math.sin(x * 0.015 + t * 3.5) * 26);
  ctx.lineTo(W + 300, 1920); ctx.closePath(); ctx.fill();
}}

function drawGrainStage(t, night) {{
  drawFieldStage(t, night);
  ctx.fillStyle = {"'#DCE8F2'" if is_snow else ("night ? '#8F6A28' : '#E2AD42'")};
  ctx.beginPath(); ctx.moveTo(-300, 1920);
  for (let x = -300; x <= W + 300; x += 60) ctx.lineTo(x, 1230 + Math.abs(x - 540) * -0.14 + Math.sin(x * 0.02 + t * 2.2) * 14);
  ctx.lineTo(W + 300, 1920); ctx.closePath(); ctx.fill();
}}

export function buildShots() {{
  const S = [], CUES = [];
  const add = (o) => (S.push(o), o);
  const cue = (t, type, o = {{}}) => CUES.push({{ t: +t.toFixed(3), type, ...o }});
  const cut = (i) => (i === 0 ? 0 : L(i) - 0.08);
{shots_body}
  return {{ shots: S, cues: CUES }};
}}
"""
    (proj_dir / "src" / "shots.js").write_text(shots_code, encoding="utf-8", newline="\n")
    main_code = _build_no_fade_main_js(["900 100px Inter", "800 92px Inter"], initial_bg="#EFE6D6")
    (proj_dir / "src" / "main.js").write_text(main_code, encoding="utf-8", newline="\n")

    safe_title_html = json.dumps(title)[1:-1].replace("<", "&lt;").replace(">", "&gt;")
    html_code = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{safe_title_html}</title>
<style>
@font-face {{ font-family: 'Inter'; font-weight: 900; src: url('fonts/Inter-Black.otf'); }}
@font-face {{ font-family: 'Inter'; font-weight: 800; src: url('fonts/Inter-ExtraBold.otf'); }}
html, body {{ margin: 0; background: #EFE6D6; height: 100%; }} body {{ display: flex; align-items: center; justify-content: center; }}
canvas {{ display: block; height: 100vh; width: auto; max-width: 100vw; object-fit: contain; }} body.capture canvas {{ height: auto; }}
#play {{ position: fixed; font: 900 28px Inter, sans-serif; padding: 18px 36px; border: 0; border-radius: 40px; background: #F2B23E; cursor: pointer; }}
</style></head>
<body><canvas id="cv" width="1080" height="1920"></canvas><button id="play" hidden>▶ PLAY</button>
<script>if (location.search.includes('capture')) document.body.className = 'capture';</script>
<script type="module" src="src/main.js"></script></body></html>
"""
    (proj_dir / "index.html").write_text(html_code, encoding="utf-8", newline="\n")

    unique_cards = list(dict.fromkeys(c for c in card_texts if c))
    manifest = {
        "run_id": str(run_id),
        "asset_seed": seed,
        "project_dir_name": proj_dir.name,
        "title": title,
        "topic": topic,
        "theme": theme_name,
        "style": "stick-story",
        "palette_id": "stick_story_daynight",
        "focal_vector": "STICK_STORY",
        "has_subcuts": has_subcuts,
        "scene_sequence": scene_sequence,
        "background_sequence": ["ROOM_DAYNIGHT"] * len(scene_sequence),
        "card_texts": unique_cards,
        "music_config": music_cfg,
        "shots_sha256": compute_text_sha256(shots_code),
        "file_hashes": {
            "src/core/kit.js": compute_text_sha256(kit_code),
            "src/shots.js": compute_text_sha256(shots_code),
            "src/main.js": compute_text_sha256(main_code),
            "tools/mix.py": compute_text_sha256(mix_code),
            "index.html": compute_text_sha256(html_code),
        },
    }
    (proj_dir / "asset_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    return theme_name, "stick_story_daynight", scene_sequence


def scaffold_styled_project(
    proj_dir: Path,
    title: str,
    topic: str,
    lines: List[Dict],
    recent_palette_ids: List[str],
    run_id: str = "auto",
    asset_seed: Optional[str] = None,
    recent_assets: Optional[List[Dict[str, Any]]] = None,
    music_config: Optional[Dict[str, Any]] = None,
    visual_plan: Optional[List[Dict[str, Any]]] = None,
    variant_offset: int = 0,
    requested_style: str = "",
) -> Tuple[str, str, List[str], str]:
    """Scaffolds a fresh project using the chosen fast-2D style engine.

    Returns:
        (theme_name, palette_id, scene_sequence, selected_style)
    """
    proj_dir = Path(proj_dir)
    proj_dir.mkdir(parents=True, exist_ok=True)
    theme_name = detect_topic_theme(topic, lines)
    seed = asset_seed or compute_asset_seed(run_id, topic, variant=variant_offset)
    m_cfg = music_config or build_music_config(theme_name, seed, recent_assets=recent_assets)

    chosen_style = select_visual_style(
        topic=topic,
        lines=lines,
        theme_name=theme_name,
        recent_assets=recent_assets,
        requested_style=requested_style,
        variant_offset=variant_offset,
    )

    if chosen_style == "paper-atlas":
        theme, pid, seq = _scaffold_paper_atlas(
            proj_dir=proj_dir, title=title, topic=topic, lines=lines,
            theme_name=theme_name, seed=seed, music_cfg=m_cfg, run_id=run_id,
        )
        return theme, pid, seq, "paper-atlas"

    if chosen_style == "stick-story":
        theme, pid, seq = _scaffold_stick_story(
            proj_dir=proj_dir, title=title, topic=topic, lines=lines,
            theme_name=theme_name, seed=seed, music_cfg=m_cfg, run_id=run_id,
        )
        return theme, pid, seq, "stick-story"

    theme, pid, seq = scaffold_2d_project(
        proj_dir=proj_dir, title=title, topic=topic, lines=lines,
        recent_palette_ids=recent_palette_ids, run_id=run_id,
        asset_seed=seed, recent_assets=recent_assets,
        music_config=m_cfg, visual_plan=visual_plan, variant_offset=variant_offset,
    )
    return theme, pid, seq, "2d-motion"
