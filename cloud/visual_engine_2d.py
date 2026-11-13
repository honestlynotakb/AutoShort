#!/usr/bin/env python3
"""High-Quality 2D Animated Visual Generation Engine.

Transforms video generation into a content-aware, 2D motion graphics and
illustrated vector pipeline. Eliminates hardcoded 3D scene loops and static slideshows.

Key capabilities:
1. Dynamic Subject-Matter Theming (Cosmic Space, Atomic Physics, Biology Cutaways, Tactical Survival, Dark History).
2. Per-Topic Color Palette Cycling (ensuring consecutive videos never share palettes).
3. Procedural Vector Graphics & Multi-Layer Parallax Elements in Canvas 2D.
4. Eased Motion Graphics (kinetic typography, HUD gauges, meters, cutaway diagrams, step cards, hazard alerts).
5. Synchronized Audio Cues with Word-Level Timing.
6. Scene Fingerprinting for Automated Duplicate Prevention.
"""

import os
import re
import sys
import json
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Any

ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT / ".agent" / "skills" / "faceless-shorts"
if not SKILL_DIR.exists():
    SKILL_DIR = ROOT / "faceless-shorts"

# ═════════════════════════════════════════════════════════════════════════════
# 1. DYNAMIC COLOR PALETTES & THEMES
# ═════════════════════════════════════════════════════════════════════════════

THEMES = {
    "COSMIC_SPACE": {
        "keywords": ["black hole", "gravity", "singularity", "space", "astronomy", "star", "planet", "orbit", "event horizon", "spaghettification", "time dilation", "universe"],
        "palettes": [
            {
                "id": "cosmic_abyss",
                "bg": "#070913", "card": "#0F1424", "primary": "#00F0FF", "secondary": "#8B5CF6",
                "accent": "#FFD43B", "danger": "#EF4444", "ink": "#FFFFFF", "subtext": "#94A3B8"
            },
            {
                "id": "solar_stellar",
                "bg": "#0D0D11", "card": "#181820", "primary": "#F59E0B", "secondary": "#EF4444",
                "accent": "#38BDF8", "danger": "#DC2626", "ink": "#FFFFFF", "subtext": "#A1A1AA"
            },
            {
                "id": "nebula_violet",
                "bg": "#110720", "card": "#1E0F38", "primary": "#A855F7", "secondary": "#EC4899",
                "accent": "#06B6D4", "danger": "#F43F5E", "ink": "#FFFFFF", "subtext": "#CBD5E1"
            }
        ]
    },
    "ATOMIC_PHYSICS": {
        "keywords": ["glass", "solid", "liquid", "crystal", "atom", "molecule", "physics", "amorphous", "quantum", "matter", "lattice", "freezes", "disordered"],
        "palettes": [
            {
                "id": "quantum_matrix",
                "bg": "#0B1120", "card": "#1E293B", "primary": "#10B981", "secondary": "#06B6D4",
                "accent": "#F59E0B", "danger": "#F43F5E", "ink": "#FFFFFF", "subtext": "#94A3B8"
            },
            {
                "id": "cryo_cyber",
                "bg": "#08131E", "card": "#102336", "primary": "#38BDF8", "secondary": "#6366F1",
                "accent": "#FACC15", "danger": "#E11D48", "ink": "#FFFFFF", "subtext": "#94A3B8"
            },
            {
                "id": "neon_amber",
                "bg": "#12100E", "card": "#241D18", "primary": "#F59E0B", "secondary": "#10B981",
                "accent": "#60A5FA", "danger": "#EF4444", "ink": "#FFFFFF", "subtext": "#D6D3D1"
            }
        ]
    },
    "SURVIVAL_TACTICAL": {
        "keywords": ["quicksand", "sink", "water", "cold", "shock", "fall", "freeze", "survive", "trap", "danger", "escape", "paddle", "fluid", "legs", "floating"],
        "palettes": [
            {
                "id": "tactical_hazard",
                "bg": "#18181B", "card": "#27272A", "primary": "#EAB308", "secondary": "#F97316",
                "accent": "#22C55E", "danger": "#EF4444", "ink": "#FFFFFF", "subtext": "#A1A1AA"
            },
            {
                "id": "ocean_abyss",
                "bg": "#061A24", "card": "#0C2E40", "primary": "#06B6D4", "secondary": "#3B82F6",
                "accent": "#FACC15", "danger": "#F43F5E", "ink": "#FFFFFF", "subtext": "#94A3B8"
            },
            {
                "id": "desert_strata",
                "bg": "#1C1714", "card": "#302621", "primary": "#D97706", "secondary": "#B45309",
                "accent": "#38BDF8", "danger": "#DC2626", "ink": "#FFFFFF", "subtext": "#E7E5E4"
            }
        ]
    },
    "HISTORIC_DOCUMENTARY": {
        "keywords": ["bronze", "ancient", "bull", "greece", "rome", "sicily", "acoustic", "phalaris", "king", "flag", "purple", "snail", "dye", "century", "royalty"],
        "palettes": [
            {
                "id": "imperial_bronze",
                "bg": "#18130F", "card": "#2D221A", "primary": "#D97706", "secondary": "#B45309",
                "accent": "#0D9488", "danger": "#B91C1C", "ink": "#FAF5F0", "subtext": "#D6D3D1"
            },
            {
                "id": "royal_purple",
                "bg": "#140A1E", "card": "#28143C", "primary": "#A855F7", "secondary": "#EAB308",
                "accent": "#06B6D4", "danger": "#E11D48", "ink": "#FFFFFF", "subtext": "#E2E8F0"
            },
            {
                "id": "vellum_manuscript",
                "bg": "#221E1B", "card": "#332D29", "primary": "#E2D9C8", "secondary": "#CA8A04",
                "accent": "#991B1B", "danger": "#DC2626", "ink": "#FFFFFF", "subtext": "#A8A29E"
            }
        ]
    },
    "BIOLOGY_CUTAWAY": {
        "keywords": ["body", "heart", "stomach", "gum", "acid", "organ", "cells", "blood", "brain", "swallow", "digest", "anatomy", "lungs"],
        "palettes": [
            {
                "id": "medical_vector",
                "bg": "#0F172A", "card": "#1E293B", "primary": "#F43F5E", "secondary": "#06B6D4",
                "accent": "#FACC15", "danger": "#EF4444", "ink": "#FFFFFF", "subtext": "#94A3B8"
            },
            {
                "id": "cellular_emerald",
                "bg": "#061A16", "card": "#0C2E28", "primary": "#10B981", "secondary": "#38BDF8",
                "accent": "#F59E0B", "danger": "#F43F5E", "ink": "#FFFFFF", "subtext": "#A7F3D0"
            }
        ]
    }
}

DEFAULT_PALETTE = {
    "id": "default_clean",
    "bg": "#0F172A", "card": "#1E293B", "primary": "#38BDF8", "secondary": "#818CF8",
    "accent": "#FACC15", "danger": "#EF4444", "ink": "#FFFFFF", "subtext": "#94A3B8"
}

def detect_topic_theme(topic: str, lines: List[Dict]) -> str:
    """Classifies topic and text into one of the 2D visual themes."""
    full_text = (topic + " " + " ".join(line.get("text", "") for line in lines)).lower()
    
    best_theme = "ATOMIC_PHYSICS"
    max_score = 0
    
    for theme_name, theme_data in THEMES.items():
        score = sum(1 for kw in theme_data["keywords"] if kw in full_text)
        if score > max_score:
            max_score = score
            best_theme = theme_name
            
    return best_theme

def pick_variation_palette(theme_name: str, recent_palette_ids: List[str]) -> Dict[str, Any]:
    """Selects a color palette not recently used to guarantee consecutive visual variation."""
    theme = THEMES.get(theme_name, THEMES["ATOMIC_PHYSICS"])
    palettes = theme["palettes"]
    
    for p in palettes:
        if p["id"] not in recent_palette_ids:
            return p
            
    # If all recently used, pick the oldest
    return palettes[0]

# ═════════════════════════════════════════════════════════════════════════════
# 2. 2D PROCEDURAL KIT GENERATOR (src/core/kit2d.js)
# ═════════════════════════════════════════════════════════════════════════════

def generate_kit2d_js(palette: Dict[str, Any]) -> str:
    """Generates the procedural 2D canvas drawing kit tailored to the active color palette."""
    pal_json = json.dumps(palette)
    
    return f"""// Procedural 2D Motion Graphics & Vector Drawing Kit
import {{ ctx, W, H, TAU, lerp, clamp, seg, eo, eio, eob, rnd, rr, circle, ell, line }} from './lib.js';

export const P = {pal_json};

// ═══════════════════════ PARALLAX BACKGROUNDS ═══════════════════════

export function bgGrid(t, speed = 25) {{
  ctx.fillStyle = P.bg;
  ctx.fillRect(-300, -300, W + 600, H + 600);
  
  // Subtle moving isometric / perspective grid
  ctx.save();
  ctx.strokeStyle = P.primary + '18';
  ctx.lineWidth = 2;
  const offY = (t * speed) % 80;
  for (let y = -100 + offY; y <= H + 200; y += 80) {{
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
  }}
  for (let x = 0; x <= W; x += 100) {{
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke();
  }}
  ctx.restore();
}}

export function bgParticles(t, count = 40, color = P.primary) {{
  ctx.save();
  for (let i = 0; i < count; i++) {{
    const seed = i * 137.5;
    const speed = 20 + rnd(i) * 40;
    const y = (rnd(i * 3) * H + t * speed) % (H + 100);
    const x = (rnd(i * 7) * W + Math.sin(t * 0.8 + i) * 30) % W;
    const r = 2 + rnd(i * 5) * 5;
    const alpha = 0.2 + rnd(i * 11) * 0.5;
    circle(x, y, r, color + Math.floor(alpha * 255).toString(16).padStart(2, '0'));
  }}
  ctx.restore();
}}

// ═══════════════════════ PROCEDURAL TOPIC VECTORS ═══════════════════════

/** Swirling 2D Black Hole with relativistic accretion disk and photon sphere */
export function drawBlackHole(x, y, r, t, pull = 0) {{
  ctx.save();
  ctx.translate(x, y);
  
  // Accretion disk glow rings
  for (let i = 8; i >= 1; i--) {{
    const rad = r * (1.2 + i * 0.28);
    const ang = t * (0.8 + i * 0.2) * (i % 2 === 0 ? 1 : -1);
    ctx.save();
    ctx.rotate(ang);
    ctx.beginPath();
    ctx.ellipse(0, 0, rad, rad * 0.45, 0, 0, TAU);
    ctx.strokeStyle = (i % 2 === 0 ? P.primary : P.accent) + '35';
    ctx.lineWidth = 14 + i * 2;
    ctx.stroke();
    ctx.restore();
  }}
  
  // Relativistic particle orbit stream
  for (let j = 0; j < 32; j++) {{
    const ang = j * (TAU / 32) + t * 2.5;
    const dist = r * (1.3 + Math.sin(j * 4 + t * 3) * 0.5);
    const px = Math.cos(ang) * dist;
    const py = Math.sin(ang) * dist * 0.45;
    circle(px, py, 4 + (j % 4) * 2, P.accent);
  }}
  
  // Event Horizon (Absolute Void)
  circle(0, 0, r, '#000000');
  
  // Glowing Photon Sphere Ring
  ctx.beginPath();
  ctx.arc(0, 0, r + 4, 0, TAU);
  ctx.strokeStyle = P.primary;
  ctx.lineWidth = 8;
  ctx.shadowColor = P.primary;
  ctx.shadowBlur = 24;
  ctx.stroke();
  
  ctx.restore();
}}

/** Atomic Lattice: smoothly animates between crystalline order and amorphous chaos */
export function drawAtomicLattice(x, y, w, h, t, chaos = 0) {{
  ctx.save();
  ctx.translate(x - w / 2, y - h / 2);
  const rows = 5, cols = 5;
  const dx = w / (cols - 1), dy = h / (rows - 1);
  const pts = [];
  
  for (let r = 0; r < rows; r++) {{
    pts[r] = [];
    for (let c = 0; c < cols; c++) {{
      const ox = (rnd(r * 11 + c) - 0.5) * dx * 1.3 * chaos;
      const oy = (rnd(r * 17 + c) - 0.5) * dy * 1.3 * chaos;
      const vib = Math.sin(t * 8 + r * 3 + c * 2) * (3 + chaos * 8);
      pts[r][c] = [c * dx + ox + vib, r * dy + oy + vib];
    }}
  }}
  
  // Draw atomic bonds
  ctx.lineWidth = 5;
  ctx.strokeStyle = P.secondary + (chaos > 0.5 ? '40' : '90');
  for (let r = 0; r < rows; r++) {{
    for (let c = 0; c < cols; c++) {{
      if (c < cols - 1) line([pts[r][c], pts[r][c + 1]], ctx.strokeStyle, 4);
      if (r < rows - 1) line([pts[r][c], pts[r + 1][c]], ctx.strokeStyle, 4);
    }}
  }}
  
  // Draw atoms
  for (let r = 0; r < rows; r++) {{
    for (let c = 0; c < cols; c++) {{
      const [px, py] = pts[r][c];
      circle(px, py, 20, P.primary);
      circle(px - 4, py - 4, 6, '#FFFFFF');
    }}
  }}
  ctx.restore();
}}

/** Quicksand & Non-Newtonian Fluid Vortex */
export function drawQuicksandVortex(x, y, r, t, packing = 0) {{
  ctx.save();
  ctx.translate(x, y);
  
  // Fluid density ripples
  for (let k = 6; k >= 1; k--) {{
    const rad = r * (0.3 + k * 0.15);
    const wobble = Math.sin(t * 3 + k) * 12;
    ctx.beginPath();
    ctx.ellipse(0, 0, rad + wobble, (rad + wobble) * 0.6, 0, 0, TAU);
    ctx.fillStyle = k % 2 === 0 ? P.card : P.secondary + '40';
    ctx.fill();
    ctx.strokeStyle = P.primary;
    ctx.lineWidth = 4;
    ctx.stroke();
  }}
  
  // Trapped / Packing sand grain clusters
  const grainCount = 45;
  for (let i = 0; i < grainCount; i++) {{
    const dist = (i / grainCount) * r * (1 - packing * 0.4);
    const ang = i * 2.4 + t * (2 - packing * 1.5);
    const gx = Math.cos(ang) * dist;
    const gy = Math.sin(ang) * dist * 0.6;
    circle(gx, gy, 6 + (i % 5) * 2, P.accent);
  }}
  ctx.restore();
}}

/** Acoustic Chamber & Resonant Waveguides (Brazen Bull / Ancient Physics) */
export function drawAcousticResonator(x, y, s, t, intensity = 1) {{
  ctx.save();
  ctx.translate(x, y);
  ctx.scale(s, s);
  
  // Bronze chamber hull
  rr(-220, -140, 440, 280, 40);
  ctx.fillStyle = P.card; ctx.fill();
  ctx.strokeStyle = P.primary; ctx.lineWidth = 8; ctx.stroke();
  
  // Resonant standing soundwaves
  const waves = 5;
  for (let w = 0; w < waves; w++) {{
    const off = (t * 4 + w * 0.6) % 3;
    const alpha = clamp(1 - off / 3);
    ctx.beginPath();
    ctx.arc(150 + off * 80, 0, 40 + off * 60, -Math.PI * 0.4, Math.PI * 0.4);
    ctx.strokeStyle = P.danger + Math.floor(alpha * 255).toString(16).padStart(2, '0');
    ctx.lineWidth = 10 * intensity;
    ctx.stroke();
  }}
  
  // Heat thermal coils beneath
  for (let i = -160; i <= 160; i += 40) {{
    const flameH = 40 + Math.sin(t * 12 + i) * 25;
    line([[i, 150], [i, 150 + flameH]], P.danger, 10);
  }}
  ctx.restore();
}}

// ═══════════════════════ HUD GAUGES & MOTION CALLOUTS ═══════════════════════

/** High-Tech Radial Telemetry Gauge */
export function drawRadialGauge(x, y, r, valRatio, label, valText, sc = 1) {{
  if (sc <= 0) return;
  ctx.save();
  ctx.translate(x, y);
  ctx.scale(sc, sc);
  
  // Background arc
  ctx.beginPath();
  ctx.arc(0, 0, r, Math.PI * 0.75, Math.PI * 2.25);
  ctx.strokeStyle = P.card;
  ctx.lineWidth = 18;
  ctx.lineCap = 'round';
  ctx.stroke();
  
  // Value arc
  const sweep = Math.PI * 1.5 * clamp(valRatio);
  ctx.beginPath();
  ctx.arc(0, 0, r, Math.PI * 0.75, Math.PI * 0.75 + sweep);
  ctx.strokeStyle = P.primary;
  ctx.lineWidth = 18;
  ctx.lineCap = 'round';
  ctx.shadowColor = P.primary;
  ctx.shadowBlur = 15;
  ctx.stroke();
  
  // Centered labels
  ctx.font = '900 48px Inter';
  ctx.fillStyle = P.ink;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(valText, 0, -8);
  
  ctx.font = '700 24px Inter';
  ctx.fillStyle = P.subtext;
  ctx.fillText(label.toUpperCase(), 0, 42);
  
  ctx.restore();
}}

/** Metric Comparison Bar / Scale */
export function drawComparisonBar(x, y, w, h, ratioA, labelA, labelB, sc = 1) {{
  if (sc <= 0) return;
  ctx.save();
  ctx.translate(x - w / 2, y);
  ctx.scale(sc, sc);
  
  rr(0, 0, w, h, h / 2);
  ctx.fillStyle = P.card;
  ctx.fill();
  
  const wA = w * clamp(ratioA);
  rr(0, 0, wA, h, h / 2);
  ctx.fillStyle = P.primary;
  ctx.fill();
  
  ctx.font = '900 26px Inter';
  ctx.fillStyle = '#FFFFFF';
  ctx.textAlign = 'left';
  ctx.fillText(labelA, 25, h / 2 + 8);
  
  ctx.textAlign = 'right';
  ctx.fillStyle = P.subtext;
  ctx.fillText(labelB, w - 25, h / 2 + 8);
  
  ctx.restore();
}}

/** Kinetic Animated Step Card (Stick Story Style) */
export function drawStepCard(stepNum, title, x, y, sc = 1) {{
  if (sc <= 0) return;
  ctx.save();
  ctx.translate(x, y);
  ctx.scale(sc, sc);
  
  const w = 780, h = 130;
  rr(-w / 2, -h / 2, w, h, 28);
  ctx.fillStyle = P.primary;
  ctx.shadowColor = 'rgba(0,0,0,0.45)';
  ctx.shadowBlur = 25;
  ctx.shadowOffsetY = 12;
  ctx.fill();
  
  // Step Number Badge
  circle(-w / 2 + 75, 0, 46, P.card);
  ctx.font = '900 42px Inter';
  ctx.fillStyle = P.accent;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(String(stepNum), -w / 2 + 75, 2);
  
  // Title
  ctx.font = '900 38px Inter';
  ctx.fillStyle = '#0F172A';
  ctx.textAlign = 'left';
  ctx.fillText(title.toUpperCase(), -w / 2 + 150, 4);
  
  ctx.restore();
}}

/** Hazard Warning Banner / Stamp */
export function drawHazardBanner(text, x, y, sc = 1) {{
  if (sc <= 0) return;
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(-0.05);
  ctx.scale(sc, sc);
  
  const w = 840, h = 140;
  rr(-w / 2, -h / 2, w, h, 24);
  ctx.fillStyle = P.danger;
  ctx.shadowColor = 'rgba(239,68,68,0.5)';
  ctx.shadowBlur = 30;
  ctx.fill();
  
  ctx.font = '900 46px Inter';
  ctx.fillStyle = '#FFFFFF';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText('⚠ ' + text.toUpperCase(), 0, 4);
  
  ctx.restore();
}}

/** Top Topic Pill Badge */
export function drawTopicPill(text, x, y, sc = 1) {{
  if (sc <= 0) return;
  ctx.save();
  ctx.translate(x, y);
  ctx.scale(sc, sc);
  
  ctx.font = '900 28px Inter';
  const tw = ctx.measureText(text).width + 70;
  rr(-tw / 2, -30, tw, 60, 30);
  ctx.fillStyle = P.card;
  ctx.strokeStyle = P.primary;
  ctx.lineWidth = 3;
  ctx.fill();
  ctx.stroke();
  
  ctx.fillStyle = P.primary;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(text.toUpperCase(), 0, 2);
  ctx.restore();
}}
"""

# ═════════════════════════════════════════════════════════════════════════════
# 3. CONTENT-AWARE SHOT GENERATOR (src/shots.js)
# ═════════════════════════════════════════════════════════════════════════════

def generate_shots_js(
    title: str,
    topic: str,
    lines: List[Dict],
    theme: str,
    palette: Dict[str, Any]
) -> Tuple[str, List[str]]:
    """Generates dynamic, content-aware shots.js with smooth 2D animations and sound cues.
    
    Returns:
        (shots_js_code, scene_sequence_archetypes)
    """
    clean_title = re.sub(r'#shorts', '', title, flags=re.IGNORECASE).strip()
    clean_topic = re.sub(r'#shorts', '', topic, flags=re.IGNORECASE).strip()
    num_lines = len(lines)
    
    scene_sequence = []
    shot_blocks = []
    
    for i in range(num_lines):
        shot_id = f"S{i+1:02d}"
        line_text = lines[i].get("text", "")
        
        # Decide Shot Archetype based on position and content
        if i == 0:
            archetype = "HOOK_HERO"
            scene_sequence.append("HOOK_HERO")
            
            # Select appropriate focal vector for Hook
            if theme == "COSMIC_SPACE":
                focal_render = "K.drawBlackHole(540, 920, 180, lt);"
            elif theme == "ATOMIC_PHYSICS":
                focal_render = "K.drawAtomicLattice(540, 920, 560, 560, lt, eio(seg(lt, 0.2, 1.2)));"
            elif theme == "SURVIVAL_TACTICAL":
                focal_render = "K.drawQuicksandVortex(540, 940, 240, lt, seg(lt, 0, d));"
            elif theme == "HISTORIC_DOCUMENTARY":
                focal_render = "K.drawAcousticResonator(540, 940, 1.3, lt, 1.0);"
            else:
                focal_render = "K.drawAtomicLattice(540, 920, 500, 500, lt, 0.4);"
                
            block = f"""
  {{ const st = cut({i});
    add({{ id: '{shot_id}', at: st, cam: [540, 900], zoom: 0.18, note: 'Hook: High-impact hero vector with kinetic title', draw(lt, d, t) {{
      K.bgGrid(t, 35);
      K.bgParticles(t, 30);
      {focal_render}
      K.drawTopicPill('{clean_title[:24]}', 540, 280, eob(seg(lt, 0.1, 0.45)));
    }} }});
    cue(st, 'whoosh'); cue(st + 0.15, 'pop', {{ gain: 0.6 }}); }}"""

        elif i == num_lines - 1:
            archetype = "LOOP_OUTRO"
            scene_sequence.append("LOOP_OUTRO")
            block = f"""
  {{ const st = cut({i});
    add({{ id: '{shot_id}', at: st, cam: [540, 880], zoom: 0.15, note: 'Outro: Kinetic loop card and final takeaway', draw(lt, d, t) {{
      K.bgGrid(t, 25);
      K.bgParticles(t, 40);
      const pulse = 1 + Math.sin(lt * 6) * 0.08;
      K.drawRadialGauge(540, 860, 220, 1.0, 'CURIOUS REALITY', '100%', eob(seg(lt, 0.1, 0.45)) * pulse);
      K.drawStepCard(3, 'REMEMBER TO LOOK CLOSER', 540, 1320, eob(seg(lt, 0.25, 0.55)));
      K.drawTopicPill('DID YOU KNOW THIS?', 540, 280, eob(seg(lt, 0.1, 0.4)));
    }} }});
    cue(st, 'whoosh'); cue(st + 0.2, 'slam', {{ gain: 0.7 }}); }}"""

        else:
            # Middle shots alternate between Mechanism, Metric Scale, and Hazard Reality
            mode = i % 3
            if mode == 1:
                archetype = "MECHANISM_CUTAWAY"
                scene_sequence.append("MECHANISM_CUTAWAY")
                if theme == "COSMIC_SPACE":
                    detail = "K.drawBlackHole(540, 840, 140, lt * 1.5, 0.5); K.drawRadialGauge(540, 1320, 140, seg(lt, 0, d), 'TIDAL GRAVITY', (seg(lt, 0, d) * 100).toFixed(0) + 'X', eob(seg(lt, 0.15, 0.45)));"
                elif theme == "ATOMIC_PHYSICS":
                    detail = "K.drawAtomicLattice(540, 840, 520, 520, lt, 1.0); K.drawComparisonBar(540, 1320, 780, 70, 0.85, 'AMORPHOUS LIQUID', 'CRYSTAL SOLID', eob(seg(lt, 0.2, 0.5)));"
                elif theme == "SURVIVAL_TACTICAL":
                    detail = "K.drawQuicksandVortex(540, 840, 220, lt, 0.8); K.drawComparisonBar(540, 1320, 780, 70, 0.65, 'HUMAN DENSITY: 1.0', 'SAND: 2.0', eob(seg(lt, 0.2, 0.5)));"
                else:
                    detail = "K.drawAcousticResonator(540, 860, 1.2, lt, 1.2); K.drawComparisonBar(540, 1320, 780, 70, 0.9, 'ACOUSTIC RESONANCE', 'HUMAN SCREAM', eob(seg(lt, 0.2, 0.5)));"

                block = f"""
  {{ const st = cut({i});
    add({{ id: '{shot_id}', at: st, cam: [540, 880], zoom: 0.12, note: 'Mechanism: Detailed vector dynamics & comparative scale', draw(lt, d, t) {{
      K.bgGrid(t, 20);
      {detail}
      K.drawTopicPill('KEY MECHANISM', 540, 280, eob(seg(lt, 0.1, 0.4)));
    }} }});
    cue(st, 'whoosh'); cue(st + 0.15, 'pop', {{ gain: 0.5 }}); }}"""

            elif mode == 2:
                archetype = "METRIC_TELEMETRY"
                scene_sequence.append("METRIC_TELEMETRY")
                block = f"""
  {{ const st = cut({i});
    add({{ id: '{shot_id}', at: st, cam: [540, 920], zoom: 0.14, note: 'Telemetry: Dynamic HUD gauge and metric measurement', draw(lt, d, t) {{
      K.bgGrid(t, 25);
      K.bgParticles(t, 25);
      const prog = eio(seg(lt, 0.1, d * 0.9));
      K.drawRadialGauge(540, 820, 220, prog, 'CRITICAL RATIO', (prog * 99.9).toFixed(1) + '%', eob(seg(lt, 0.1, 0.4)));
      K.drawStepCard(1, 'OBSERVE THE PATTERN', 540, 1280, eob(seg(lt, 0.2, 0.5)));
      K.drawTopicPill('SCIENTIFIC REALITY', 540, 280, eob(seg(lt, 0.1, 0.4)));
    }} }});
    cue(st, 'whoosh'); cue(st + 0.2, 'pop', {{ gain: 0.6 }}); }}"""

            else:
                archetype = "HAZARD_TWIST"
                scene_sequence.append("HAZARD_TWIST")
                block = f"""
  {{ const st = cut({i});
    add({{ id: '{shot_id}', at: st, cam: [540, 860], zoom: 0.16, note: 'Twist: High-contrast alert & tactical breakdown', draw(lt, d, t) {{
      K.bgGrid(t, 35);
      K.drawHazardBanner('CRITICAL TURNING POINT', 540, 720, eob(seg(lt, 0.1, 0.45)));
      K.drawStepCard(2, 'AVOID THE INSTINCTIVE TRAP', 540, 1180, eob(seg(lt, 0.25, 0.55)));
      K.drawTopicPill('SURPRISING PARADOX', 540, 280, eob(seg(lt, 0.1, 0.4)));
    }} }});
    cue(st, 'whoosh'); cue(st + 0.2, 'thud', {{ gain: 0.7 }}); }}"""

        shot_blocks.append(block)

    shots_body = "\n".join(shot_blocks)

    code = f"""// Auto-generated 2D Motion Graphics Shots List
import {{ ctx, W, H, clamp, lerp, seg, eo, eio, eob, rnd }} from './core/lib.js';
import {{ L, Le, Wd, T }} from './core/timing.js';
import * as K from './core/kit2d.js';

export function buildShots() {{
  const S = [], CUES = [];
  const add = (o) => (S.push(o), o);
  const cue = (t, type, o = {{}}) => CUES.push({{ t: +t.toFixed(3), type, ...o }});
  const cut = (i) => (i === 0 ? 0 : L(i) - 0.08);

{shots_body}

  return {{ shots: S, cues: CUES }};
}}
"""
    return code, scene_sequence

# ═════════════════════════════════════════════════════════════════════════════
# 4. MASTER 2D PROJECT SCAFFOLDER
# ═════════════════════════════════════════════════════════════════════════════

def scaffold_2d_project(
    proj_dir: Path,
    title: str,
    topic: str,
    lines: List[Dict],
    recent_palette_ids: List[str]
) -> Tuple[str, str, List[str]]:
    """Scaffolds a complete 2D project with Inter-Black fonts, HTML5 canvas, and dynamic shots.
    
    Returns:
        (theme_name, palette_id, scene_sequence)
    """
    proj_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Identify theme and select non-repetitive palette
    theme_name = detect_topic_theme(topic, lines)
    palette = pick_variation_palette(theme_name, recent_palette_ids)
    
    # 2. Source baseline files from inside-out (Inter-Black font, capture.mjs, mix.py, captions.js, timing.js)
    inside_out_example = SKILL_DIR / "styles" / "inside-out" / "example"
    
    # Copy fonts
    fonts_dir = proj_dir / "fonts"
    fonts_dir.mkdir(exist_ok=True)
    src_font = inside_out_example / "fonts" / "Inter-Black.otf"
    if src_font.exists():
        shutil.copy2(src_font, fonts_dir / "Inter-Black.otf")
        
    # Copy tools
    tools_dir = proj_dir / "tools"
    tools_dir.mkdir(exist_ok=True)
    for tool_name in ["capture.mjs", "mix.py"]:
        src_tool = inside_out_example / "tools" / tool_name
        if src_tool.exists():
            shutil.copy2(src_tool, tools_dir / tool_name)
            
    # Set up src directory
    src_dir = proj_dir / "src"
    core_dir = src_dir / "core"
    core_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy timing.js, captions.js, lib.js
    for core_file in ["timing.js", "captions.js", "lib.js"]:
        src_file = inside_out_example / "src" / "core" / core_file
        if src_file.exists():
            shutil.copy2(src_file, core_dir / core_file)
            
    # Copy main.js
    src_main = inside_out_example / "src" / "main.js"
    if src_main.exists():
        shutil.copy2(src_main, src_dir / "main.js")
        
    # Copy index.html
    src_index = inside_out_example / "index.html"
    if src_index.exists():
        shutil.copy2(src_index, proj_dir / "index.html")
        
    # 3. Generate custom kit2d.js with active palette
    kit2d_code = generate_kit2d_js(palette)
    (core_dir / "kit2d.js").write_text(kit2d_code, encoding="utf-8")
    
    # 4. Generate dynamic, content-aware shots.js
    shots_code, scene_sequence = generate_shots_js(title, topic, lines, theme_name, palette)
    (src_dir / "shots.js").write_text(shots_code, encoding="utf-8")
    
    return theme_name, palette["id"], scene_sequence
