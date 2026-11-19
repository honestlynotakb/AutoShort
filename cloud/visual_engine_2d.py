#!/usr/bin/env python3
"""High-Quality 2D Animated Visual Generation Engine.

Transforms video generation into a content-aware, 2D motion graphics and
illustrated vector pipeline. Eliminates hardcoded 3D scene loops and static slideshows.

Key capabilities:
1. Dynamic Subject-Matter Theming (Cosmic Space, Atomic Physics, Biology Cutaways, Tactical Survival, Dark History).
2. Per-Topic Color Palette Cycling (ensuring consecutive videos never share palettes).
3. 12+ Procedural Vector Graphics & Multi-Layer Parallax Elements in Canvas 2D.
4. Eased Motion Graphics (kinetic typography, HUD gauges, meters, cutaway diagrams, step cards, hazard alerts).
5. Synchronized Audio Cues with Word-Level Timing.
6. Gate 3 Pre-Render Composition & Visual Diversity Verification.
"""
from __future__ import annotations

import os
import re
import sys
import json
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT / "faceless-shorts"
if not SKILL_DIR.exists():
    SKILL_DIR = ROOT / ".agent" / "skills" / "faceless-shorts"

# ═════════════════════════════════════════════════════════════════════════════
# 1. DYNAMIC COLOR PALETTES & THEMES
# ═════════════════════════════════════════════════════════════════════════════

THEMES = {
    "COSMIC_SPACE": {
        "keywords": ["black hole", "gravity", "singularity", "space", "astronomy", "star", "planet", "orbit", "event horizon", "spaghettification", "time dilation", "universe", "rogue", "magnetar", "pulsar", "nebula", "roche", "sun", "moon", "neptune", "uranus"],
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
            },
            {
                "id": "deep_aurora",
                "bg": "#05131A", "card": "#0C232E", "primary": "#10B981", "secondary": "#06B6D4",
                "accent": "#FACC15", "danger": "#E11D48", "ink": "#FFFFFF", "subtext": "#94A3B8"
            }
        ]
    },
    "ATOMIC_PHYSICS": {
        "keywords": ["glass", "solid", "liquid", "crystal", "atom", "molecule", "physics", "amorphous", "quantum", "matter", "lattice", "freezes", "disordered", "prince rupert", "oobleck", "helium", "superfluid", "leidenfrost", "aerogel", "gallium", "cavitation", "shrimp", "ferrofluid", "mpemba", "triboluminescence", "invisibility", "cloak", "prism"],
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
            },
            {
                "id": "plasma_electric",
                "bg": "#0C0A1E", "card": "#181438", "primary": "#8B5CF6", "secondary": "#3B82F6",
                "accent": "#10B981", "danger": "#EF4444", "ink": "#FFFFFF", "subtext": "#C7D2FE"
            }
        ]
    },
    "SURVIVAL_TACTICAL": {
        "keywords": ["quicksand", "sink", "water", "cold", "shock", "fall", "freeze", "survive", "trap", "danger", "escape", "paddle", "fluid", "legs", "floating", "elevator", "car", "submerged", "rip current", "shoreline", "polar bear", "liver", "hypothermia", "undressing", "ants", "desert"],
        "palettes": [
            {
                "id": "tactical_hazard",
                "bg": "#18181B", "card": "#27272A", "primary": "#EAB308", "secondary": "#F97316",
                "accent": "#22C55E", "danger": "#EF4444", "ink": "#FFFFFF", "subtext": "#A1A1AA"
            },
            {
                "id": "oceanic_abyss",
                "bg": "#081C24", "card": "#0F3240", "primary": "#06B6D4", "secondary": "#3B82F6",
                "accent": "#F59E0B", "danger": "#EF4444", "ink": "#FFFFFF", "subtext": "#BAE6FD"
            },
            {
                "id": "arctic_frost",
                "bg": "#0F172A", "card": "#1E293B", "primary": "#38BDF8", "secondary": "#94A3B8",
                "accent": "#F43F5E", "danger": "#DC2626", "ink": "#FFFFFF", "subtext": "#E2E8F0"
            }
        ]
    },
    "HISTORIC_DOCUMENTARY": {
        "keywords": ["history", "ancient", "greek", "bronze", "bull", "sicily", "acoustic", "flag", "purple", "dye", "snails", "gold", "royalty", "emperor", "torture", "phalaris", "dancing plague", "beer flood", "byford dolphin", "halifax", "explosion", "mayan", "pyramid", "mozambique", "nepal"],
        "palettes": [
            {
                "id": "bronze_antiquity",
                "bg": "#17120E", "card": "#2C2017", "primary": "#D97706", "secondary": "#B45309",
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
    return palettes[0]


# ═════════════════════════════════════════════════════════════════════════════
# 2. CONTENT-AWARE FOCAL VECTOR ROUTER
# ═════════════════════════════════════════════════════════════════════════════

def has_keyword(text: str, keywords: List[str]) -> bool:
    """Checks if any keyword matches as a full word or defined subphrase."""
    for kw in keywords:
        if " " in kw:
            if kw in text:
                return True
        else:
            if re.search(r'\b' + re.escape(kw) + r'\b', text):
                return True
    return False


def detect_topic_focal_vector(topic: str, lines: List[Dict]) -> Tuple[str, str, str]:
    """Selects the most appropriate procedural vector based on topic subject keywords.

    Returns:
        (vector_name, hook_draw_call, mechanism_draw_call)
    """
    text = (topic + " " + " ".join(l.get("text", "") for l in lines)).lower()

    # 1. Thermal Gradient & Biological Shock (Cold Water, Lightning, Undressing)
    if has_keyword(text, ["cold water", "shock", "hypothermia", "undressing", "lightning", "lichtenberg", "blood", "armstrong"]):
        return (
            "THERMAL_GRADIENT",
            "K.drawThermalGradient(540, 920, 440, 420, seg(lt, 0, d), lt);",
            "K.drawThermalGradient(540, 840, 400, 380, 0.9, lt * 1.5); K.drawRadialGauge(540, 1320, 140, seg(lt, 0, d), 'CORE TEMPERATURE', (37 - seg(lt, 0, d) * 10).toFixed(1) + '°C', eob(seg(lt, 0.15, 0.45)));"
        )

    # 2. Black Hole / Gravitational Singularity
    if has_keyword(text, ["black hole", "singularity", "event horizon", "spaghettification", "spaghetti"]):
        return (
            "BLACK_HOLE",
            "K.drawBlackHole(540, 920, 180, lt);",
            "K.drawBlackHole(540, 840, 140, lt * 1.5, 0.5); K.drawRadialGauge(540, 1320, 140, seg(lt, 0, d), 'TIDAL GRAVITY', (seg(lt, 0, d) * 100).toFixed(0) + 'X', eob(seg(lt, 0.15, 0.45)));"
        )

    # 3. Neutron Star / Magnetar / Cosmic Radiance
    if has_keyword(text, ["magnetar", "neutron star", "pulsar", "starquake", "magnetic field", "boomerang"]):
        return (
            "NEUTRON_STAR",
            "K.drawNeutronStar(540, 920, 140, lt, 1.2);",
            "K.drawNeutronStar(540, 840, 110, lt * 2, 1.5); K.drawRadialGauge(540, 1320, 140, seg(lt, 0, d), 'MAGNETIC FLUX', '10^15 G', eob(seg(lt, 0.15, 0.45)));"
        )

    # 4. Planetary Orbits / Exoplanets / Roche Limit / Vanished Sun
    if has_keyword(text, ["planet", "orbit", "solar system", "roche", "sun", "moon", "titan", "neptune", "uranus"]):
        return (
            "PLANETARY_ORBIT",
            "K.drawPlanetaryOrbit(540, 920, 240, lt, 4);",
            "K.drawPlanetaryOrbit(540, 840, 200, lt * 1.3, 3); K.drawComparisonBar(540, 1320, 780, 70, 0.75, 'ORBITAL RADIUS', 'ROCHE LIMIT', eob(seg(lt, 0.2, 0.5)));"
        )

    # 5. Asteroid Shards / Halifax Explosion / Cosmic Dust
    if has_keyword(text, ["asteroid", "dust", "diamond rain", "meteor", "halifax", "explosion", "blast"]):
        return (
            "ASTEROID_FIELD",
            "K.drawAsteroidField(540, 920, 600, 500, lt, 35);",
            "K.drawAsteroidField(540, 840, 560, 440, lt * 1.5, 45); K.drawRadialGauge(540, 1320, 140, seg(lt, 0, d), 'IMPACT PRESSURE', (seg(lt, 0, d) * 50).toFixed(0) + ' GPa', eob(seg(lt, 0.15, 0.45)));"
        )

    # 6. Navigational Compass / Flags / Rip Current Survival Navigation / Ants
    if has_keyword(text, ["flag", "nepal", "mozambique", "purple", "dye", "snails", "ant", "desert", "navigate", "navigation", "polarization", "rip current", "shoreline", "current", "swim", "swimmer"]):
        return (
            "TELEMETRY_COMPASS",
            "K.drawTelemetryCompass(540, 920, 190, lt * 0.4, lt);",
            "K.drawTelemetryCompass(540, 840, 160, lt * 0.6, lt); K.drawComparisonBar(540, 1320, 780, 70, 0.85, 'ESCAPE BEARING', 'PARALLEL 90°', eob(seg(lt, 0.2, 0.5)));"
        )

    # 7. Submerged Vehicle & Structural Cabin Escape (Elevator / Sinking Car)
    if has_keyword(text, ["car", "elevator", "submerged", "door", "pressure", "hydrostatic"]):
        return (
            "SUBMERGED_CABIN",
            "K.drawSubmergedCabin(540, 920, 480, 360, lt, seg(lt, 0, d));",
            "K.drawSubmergedCabin(540, 840, 440, 320, lt, 0.85); K.drawRadialGauge(540, 1320, 140, seg(lt, 0, d), 'CABIN PRESSURE', (seg(lt, 0, d) * 10).toFixed(1) + ' BAR', eob(seg(lt, 0.15, 0.45)));"
        )

    # 8. Atomic Lattice & Molecular Crystals (Glass / Solids)
    if has_keyword(text, ["glass", "crystal", "amorphous", "solid", "rupert", "lattice"]):
        return (
            "ATOMIC_LATTICE",
            "K.drawAtomicLattice(540, 920, 560, 560, lt, eio(seg(lt, 0.2, 1.2)));",
            "K.drawAtomicLattice(540, 840, 520, 520, lt, 1.0); K.drawComparisonBar(540, 1320, 780, 70, 0.85, 'AMORPHOUS LIQUID', 'CRYSTAL SOLID', eob(seg(lt, 0.2, 0.5)));"
        )

    # 8. Molecular Brownian Simulation (Helium, Nitrogen, Temperature, Mpemba)
    if has_keyword(text, ["helium", "superfluid", "nitrogen", "leidenfrost", "mpemba", "aerogel", "temperature", "kelvin", "boil"]):
        return (
            "MOLECULAR_SIM",
            "K.drawMolecularSimulation(540, 920, 240, lt, 1.5);",
            "K.drawMolecularSimulation(540, 840, 200, lt * 1.4, 2.0); K.drawRadialGauge(540, 1320, 140, seg(lt, 0, d), 'THERMAL MOTION', (seg(lt, 0, d) * 300).toFixed(0) + ' K', eob(seg(lt, 0.15, 0.45)));"
        )

    # 9. Prism Refraction & Optical Cloaking (Tape, Invisibility, Light)
    if has_keyword(text, ["prism", "light", "optic", "cloak", "tape", "triboluminescence", "invisibility", "tunneling"]):
        return (
            "PRISM_REFRACTION",
            "K.drawPrismRefraction(540, 920, 180, lt);",
            "K.drawPrismRefraction(540, 840, 150, lt * 1.2); K.drawComparisonBar(540, 1320, 780, 70, 0.9, 'WAVELENGTH 450nm', 'REFRACTIVE -1.4', eob(seg(lt, 0.2, 0.5)));"
        )

    # 10. Quicksand Vortex / Fluid Entrapment
    if has_keyword(text, ["quicksand", "sink", "sand", "oobleck", "non-newtonian"]):
        return (
            "QUICKSAND_VORTEX",
            "K.drawQuicksandVortex(540, 940, 240, lt, seg(lt, 0, d));",
            "K.drawQuicksandVortex(540, 840, 220, lt, 0.8); K.drawComparisonBar(540, 1320, 780, 70, 0.65, 'HUMAN DENSITY: 1.0', 'SAND: 2.0', eob(seg(lt, 0.2, 0.5)));"
        )


    # 12. Acoustic Wave Chamber (Brazen Bull / Mayan Pyramids)
    if has_keyword(text, ["brazen bull", "acoustic", "pyramid", "mayan", "echo", "sound", "chirp"]):
        return (
            "ACOUSTIC_RESONATOR",
            "K.drawAcousticResonator(540, 940, 1.3, lt, 1.0);",
            "K.drawAcousticResonator(540, 860, 1.2, lt, 1.2); K.drawComparisonBar(540, 1320, 780, 70, 0.9, 'ACOUSTIC RESONANCE', 'DIFFRACTION ECHO', eob(seg(lt, 0.2, 0.5)));"
        )

    # Default fallback: Atomic Lattice
    return (
        "ATOMIC_LATTICE",
        "K.drawAtomicLattice(540, 920, 500, 500, lt, 0.4);",
        "K.drawAtomicLattice(540, 840, 460, 460, lt, 0.8); K.drawRadialGauge(540, 1320, 140, 0.8, 'PHYSICAL RATIO', '99.9%', eob(seg(lt, 0.15, 0.45)));"
    )


# ═════════════════════════════════════════════════════════════════════════════
# 3. 2D PROCEDURAL KIT GENERATOR (src/core/kit2d.js)
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
    const speed = 20 + rnd(i) * 40;
    const y = (rnd(i * 3) * H + t * speed) % (H + 100);
    const x = (rnd(i * 7) * W + Math.sin(t * 0.8 + i) * 30) % W;
    const r = 2 + rnd(i * 5) * 5;
    const alpha = 0.2 + rnd(i * 11) * 0.5;
    circle(x, y, r, color + Math.floor(alpha * 255).toString(16).padStart(2, '0'));
  }}
  ctx.restore();
}}

export function bgConcentricWaves(t, count = 5, color = P.secondary) {{
  ctx.save();
  for (let i = 0; i < count; i++) {{
    const rad = ((t * 40 + i * 200) % 1200);
    const alpha = clamp(1 - rad / 1200) * 0.25;
    ctx.beginPath();
    ctx.arc(W / 2, H / 2, rad, 0, TAU);
    ctx.strokeStyle = color + Math.floor(alpha * 255).toString(16).padStart(2, '0');
    ctx.lineWidth = 3;
    ctx.stroke();
  }}
  ctx.restore();
}}

// ═══════════════════════ PROCEDURAL TOPIC VECTORS ═══════════════════════

/** Swirling 2D Black Hole with accretion disk */
export function drawBlackHole(x, y, r, t, pull = 0) {{
  ctx.save();
  ctx.translate(x, y);
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
  circle(0, 0, r, '#000000');
  ctx.beginPath();
  ctx.arc(0, 0, r + 4, 0, TAU);
  ctx.strokeStyle = P.primary;
  ctx.lineWidth = 8;
  ctx.shadowColor = P.primary;
  ctx.shadowBlur = 24;
  ctx.stroke();
  ctx.restore();
}}

/** Spinning Neutron Star / Pulsar with Relativistic Cones */
export function drawNeutronStar(x, y, r, t, beam = 1) {{
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(t * 1.5);
  // Bipolar emission light cones
  ctx.save();
  ctx.fillStyle = P.primary + '40';
  ctx.beginPath();
  ctx.moveTo(0, 0); ctx.lineTo(-120 * beam, -400); ctx.lineTo(120 * beam, -400); ctx.closePath();
  ctx.fill();
  ctx.beginPath();
  ctx.moveTo(0, 0); ctx.lineTo(-120 * beam, 400); ctx.lineTo(120 * beam, 400); ctx.closePath();
  ctx.fill();
  ctx.restore();
  // Central hyper-dense core
  circle(0, 0, r, P.primary);
  circle(0, 0, r * 0.7, '#FFFFFF');
  ctx.restore();
}}

/** Planetary Orbit & Exoplanet Revolution */
export function drawPlanetaryOrbit(x, y, r, t, count = 3) {{
  ctx.save();
  ctx.translate(x, y);
  // Central Star
  circle(0, 0, 50, P.accent);
  for (let i = 1; i <= count; i++) {{
    const rad = r * (0.4 + i * 0.28);
    ctx.beginPath();
    ctx.arc(0, 0, rad, 0, TAU);
    ctx.strokeStyle = P.primary + '40';
    ctx.lineWidth = 3;
    ctx.stroke();
    const ang = t * (1.2 / i) + i * 2.1;
    const px = Math.cos(ang) * rad, py = Math.sin(ang) * rad;
    circle(px, py, 14 + i * 4, i % 2 === 0 ? P.primary : P.secondary);
  }}
  ctx.restore();
}}

/** Drifting Asteroid Field */
export function drawAsteroidField(x, y, w, h, t, speed = 30) {{
  ctx.save();
  ctx.translate(x, y);
  for (let i = 0; i < 18; i++) {{
    const ox = ((rnd(i * 13) * w + t * speed * (0.8 + rnd(i))) % w) - w / 2;
    const oy = ((rnd(i * 29) * h + Math.sin(t + i) * 40) % h) - h / 2;
    const s = 15 + rnd(i * 7) * 25;
    ctx.save();
    ctx.translate(ox, oy);
    ctx.rotate(t * 0.5 + i);
    rr(-s/2, -s/2, s, s, 6);
    ctx.fillStyle = P.card;
    ctx.strokeStyle = P.primary;
    ctx.lineWidth = 3;
    ctx.fill(); ctx.stroke();
    ctx.restore();
  }}
  ctx.restore();
}}

/** Atomic Lattice with Order vs Disorder */
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
  ctx.lineWidth = 5;
  ctx.strokeStyle = P.secondary + (chaos > 0.5 ? '40' : '90');
  for (let r = 0; r < rows; r++) {{
    for (let c = 0; c < cols; c++) {{
      if (c < cols - 1) line([pts[r][c], pts[r][c + 1]], ctx.strokeStyle, 4);
      if (r < rows - 1) line([pts[r][c], pts[r + 1][c]], ctx.strokeStyle, 4);
    }}
  }}
  for (let r = 0; r < rows; r++) {{
    for (let c = 0; c < cols; c++) {{
      const [px, py] = pts[r][c];
      circle(px, py, 20, P.primary);
      circle(px - 4, py - 4, 6, '#FFFFFF');
    }}
  }}
  ctx.restore();
}}

/** Thermal Brownian Molecular Simulation */
export function drawMolecularSimulation(x, y, r, t, speed = 1) {{
  ctx.save();
  ctx.translate(x, y);
  circle(0, 0, r, P.card);
  ctx.strokeStyle = P.primary;
  ctx.lineWidth = 6; ctx.stroke();
  for (let i = 0; i < 24; i++) {{
    const ang = rnd(i * 17) * TAU + t * speed * (rnd(i * 3) - 0.5) * 4;
    const dist = (rnd(i * 31) * (r - 30));
    const px = Math.cos(ang) * dist, py = Math.sin(ang) * dist;
    circle(px, py, 12, i % 2 === 0 ? P.primary : P.accent);
  }}
  ctx.restore();
}}

/** Optical Prism Light Refraction */
export function drawPrismRefraction(x, y, r, t) {{
  ctx.save();
  ctx.translate(x, y);
  // Triangular crystal prism
  ctx.beginPath();
  ctx.moveTo(0, -r); ctx.lineTo(r, r * 0.8); ctx.lineTo(-r, r * 0.8); ctx.closePath();
  ctx.fillStyle = P.card + 'C0'; ctx.fill();
  ctx.strokeStyle = P.primary; ctx.lineWidth = 6; ctx.stroke();
  // Incoming white beam
  line([[-260, 40], [0, 0]], '#FFFFFF', 8);
  // Outgoing refracted rainbow fan
  const colors = [P.danger, P.accent, P.primary, P.secondary];
  for (let i = 0; i < colors.length; i++) {{
    const yOff = -30 + i * 35;
    line([[0, 0], [280, yOff]], colors[i], 8);
  }}
  ctx.restore();
}}

/** Quicksand Vortex */
export function drawQuicksandVortex(x, y, r, t, packing = 0) {{
  ctx.save();
  ctx.translate(x, y);
  for (let k = 6; k >= 1; k--) {{
    const rad = r * (0.3 + k * 0.15);
    const wobble = Math.sin(t * 3 + k) * 12;
    ctx.beginPath();
    ctx.ellipse(0, 0, rad + wobble, (rad + wobble) * 0.6, 0, 0, TAU);
    ctx.fillStyle = k % 2 === 0 ? P.card : P.secondary + '40';
    ctx.fill();
    ctx.strokeStyle = P.primary; ctx.lineWidth = 4; ctx.stroke();
  }}
  for (let i = 0; i < 40; i++) {{
    const dist = (i / 40) * r * (1 - packing * 0.4);
    const ang = i * 2.4 + t * (2 - packing * 1.5);
    circle(Math.cos(ang) * dist, Math.sin(ang) * dist * 0.6, 6, P.accent);
  }}
  ctx.restore();
}}

/** Submerged Cabin Escape Diagram */
export function drawSubmergedCabin(x, y, w, h, t, fill = 0.5) {{
  ctx.save();
  ctx.translate(x, y);
  rr(-w/2, -h/2, w, h, 20);
  ctx.fillStyle = P.card; ctx.fill();
  ctx.strokeStyle = P.primary; ctx.lineWidth = 8; ctx.stroke();
  // Rising water level
  const waterH = h * clamp(fill);
  ctx.save();
  ctx.beginPath();
  rr(-w/2, h/2 - waterH, w, waterH, 10);
  ctx.fillStyle = P.secondary + '60'; ctx.fill();
  ctx.restore();
  // Hydrostatic pressure arrows
  for (let i = -h/2 + 40; i <= h/2 - 40; i += 50) {{
    line([[-w/2 - 60, i], [-w/2 - 10, i]], P.danger, 6);
  }}
  ctx.restore();
}}

/** Acoustic Chamber & Resonator */
export function drawAcousticResonator(x, y, s, t, intensity = 1) {{
  ctx.save();
  ctx.translate(x, y); ctx.scale(s, s);
  rr(-220, -140, 440, 280, 40);
  ctx.fillStyle = P.card; ctx.fill();
  ctx.strokeStyle = P.primary; ctx.lineWidth = 8; ctx.stroke();
  for (let w = 0; w < 5; w++) {{
    const off = (t * 4 + w * 0.6) % 3;
    const alpha = clamp(1 - off / 3);
    ctx.beginPath();
    ctx.arc(150 + off * 80, 0, 40 + off * 60, -Math.PI * 0.4, Math.PI * 0.4);
    ctx.strokeStyle = P.danger + Math.floor(alpha * 255).toString(16).padStart(2, '0');
    ctx.lineWidth = 10 * intensity; ctx.stroke();
  }}
  ctx.restore();
}}

/** Thermal Vascular Gradient */
export function drawThermalGradient(x, y, w, h, coldRatio = 0.5, t = 0) {{
  ctx.save();
  ctx.translate(x, y);
  // Human torso silhouette outline
  rr(-w/2, -h/2, w, h, 60);
  ctx.fillStyle = P.card; ctx.fill();
  ctx.strokeStyle = P.primary; ctx.lineWidth = 6; ctx.stroke();
  // Core heat vs peripheral chill
  const coreR = (w / 3) * (1 - coldRatio * 0.4);
  circle(0, -20, coreR, P.danger + '80');
  circle(0, -20, coreR * 0.5, P.accent);
  // Constricted peripheral veins
  for (let i = -w/2 + 30; i <= w/2 - 30; i += 40) {{
    line([[i, -h/2 + 20], [i, h/2 - 20]], P.primary + '40', 4);
  }}
  ctx.restore();
}}

/** Navigational Telemetry Compass */
export function drawTelemetryCompass(x, y, r, heading = 0, t = 0) {{
  ctx.save();
  ctx.translate(x, y);
  circle(0, 0, r, P.card);
  ctx.strokeStyle = P.primary; ctx.lineWidth = 6; ctx.stroke();
  ctx.save();
  ctx.rotate(heading);
  line([[0, -r + 20], [0, r - 20]], P.accent, 6);
  line([[-r + 20, 0], [r - 20, 0]], P.secondary, 4);
  circle(0, 0, 16, P.primary);
  ctx.restore();
  ctx.restore();
}}

// ═══════════════════════ HUD GAUGES & MOTION CALLOUTS ═══════════════════════

export function drawRadialGauge(x, y, r, valRatio, label, valText, sc = 1) {{
  if (sc <= 0) return;
  ctx.save();
  ctx.translate(x, y); ctx.scale(sc, sc);
  ctx.beginPath();
  ctx.arc(0, 0, r, Math.PI * 0.75, Math.PI * 2.25);
  ctx.strokeStyle = P.card; ctx.lineWidth = 18; ctx.lineCap = 'round'; ctx.stroke();
  const sweep = Math.PI * 1.5 * clamp(valRatio);
  ctx.beginPath();
  ctx.arc(0, 0, r, Math.PI * 0.75, Math.PI * 0.75 + sweep);
  ctx.strokeStyle = P.primary; ctx.lineWidth = 18; ctx.lineCap = 'round';
  ctx.shadowColor = P.primary; ctx.shadowBlur = 15; ctx.stroke();
  ctx.font = '900 48px Inter'; ctx.fillStyle = P.ink; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.fillText(valText, 0, -8);
  ctx.font = '700 24px Inter'; ctx.fillStyle = P.subtext;
  ctx.fillText(label.toUpperCase(), 0, 42);
  ctx.restore();
}}

export function drawComparisonBar(x, y, w, h, ratioA, labelA, labelB, sc = 1) {{
  if (sc <= 0) return;
  ctx.save();
  ctx.translate(x - w / 2, y); ctx.scale(sc, sc);
  rr(0, 0, w, h, h / 2);
  ctx.fillStyle = P.card; ctx.fill();
  const wA = w * clamp(ratioA);
  rr(0, 0, wA, h, h / 2);
  ctx.fillStyle = P.primary; ctx.fill();
  ctx.font = '900 26px Inter'; ctx.fillStyle = '#FFFFFF'; ctx.textAlign = 'left';
  ctx.fillText(labelA, 25, h / 2 + 8);
  ctx.textAlign = 'right'; ctx.fillStyle = P.subtext;
  ctx.fillText(labelB, w - 25, h / 2 + 8);
  ctx.restore();
}}

export function drawStepCard(stepNum, title, x, y, sc = 1) {{
  if (sc <= 0) return;
  ctx.save();
  ctx.translate(x, y); ctx.scale(sc, sc);
  const w = 780, h = 130;
  rr(-w / 2, -h / 2, w, h, 28);
  ctx.fillStyle = P.primary; ctx.shadowColor = 'rgba(0,0,0,0.45)';
  ctx.shadowBlur = 25; ctx.shadowOffsetY = 12; ctx.fill();
  circle(-w / 2 + 75, 0, 46, P.card);
  ctx.font = '900 42px Inter'; ctx.fillStyle = P.accent; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.fillText(String(stepNum), -w / 2 + 75, 2);
  ctx.font = '900 38px Inter'; ctx.fillStyle = '#0F172A'; ctx.textAlign = 'left';
  ctx.fillText(title.toUpperCase(), -w / 2 + 150, 4);
  ctx.restore();
}}

export function drawHazardBanner(text, x, y, sc = 1) {{
  if (sc <= 0) return;
  ctx.save();
  ctx.translate(x, y); ctx.rotate(-0.05); ctx.scale(sc, sc);
  const w = 840, h = 140;
  rr(-w / 2, -h / 2, w, h, 24);
  ctx.fillStyle = P.danger; ctx.shadowColor = 'rgba(239,68,68,0.5)'; ctx.shadowBlur = 30; ctx.fill();
  ctx.font = '900 46px Inter'; ctx.fillStyle = '#FFFFFF'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.fillText('⚠ ' + text.toUpperCase(), 0, 4);
  ctx.restore();
}}

export function drawTopicPill(text, x, y, sc = 1) {{
  if (sc <= 0) return;
  ctx.save();
  ctx.translate(x, y); ctx.scale(sc, sc);
  ctx.font = '900 28px Inter';
  const tw = ctx.measureText(text).width + 70;
  rr(-tw / 2, -30, tw, 60, 30);
  ctx.fillStyle = P.card; ctx.strokeStyle = P.primary; ctx.lineWidth = 3; ctx.fill(); ctx.stroke();
  ctx.fillStyle = P.primary; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.fillText(text.toUpperCase(), 0, 2);
  ctx.restore();
}}
"""


# ═════════════════════════════════════════════════════════════════════════════
# 4. CONTENT-AWARE SHOT GENERATOR (src/shots.js)
# ═════════════════════════════════════════════════════════════════════════════

def generate_shots_js(
    title: str,
    topic: str,
    lines: List[Dict],
    theme: str,
    palette: Dict[str, Any]
) -> Tuple[str, List[str], str]:
    """Generates dynamic, content-aware shots.js with smooth 2D animations and sound cues.

    Returns:
        (shots_js_code, scene_sequence_archetypes, focal_vector_name)
    """
    clean_title = re.sub(r'#shorts', '', title, flags=re.IGNORECASE).strip()
    num_lines = len(lines)

    vector_name, hook_draw, mech_draw = detect_topic_focal_vector(topic, lines)

    scene_sequence = []
    shot_blocks = []

    for i in range(num_lines):
        shot_id = f"S{i+1:02d}"

        if i == 0:
            archetype = f"HOOK_{vector_name}"
            scene_sequence.append(archetype)
            block = f"""
  {{ const st = cut({i});
    add({{ id: '{shot_id}', at: st, cam: [540, 900], zoom: 0.18, note: 'Hook: High-impact hero vector with kinetic title', draw(lt, d, t) {{
      K.bgGrid(t, 35);
      K.bgParticles(t, 30);
      {hook_draw}
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
            mode = i % 3
            if mode == 1:
                archetype = f"MECH_{vector_name}"
                scene_sequence.append(archetype)
                block = f"""
  {{ const st = cut({i});
    add({{ id: '{shot_id}', at: st, cam: [540, 880], zoom: 0.12, note: 'Mechanism: Detailed vector dynamics & comparative scale', draw(lt, d, t) {{
      K.bgGrid(t, 20);
      {mech_draw}
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
    return code, scene_sequence, vector_name


# ═════════════════════════════════════════════════════════════════════════════
# 5. MASTER 2D PROJECT SCAFFOLDER
# ═════════════════════════════════════════════════════════════════════════════

def scaffold_2d_project(
    proj_dir: Path,
    title: str,
    topic: str,
    lines: List[Dict],
    recent_palette_ids: List[str]
) -> Tuple[str, str, List[str]]:
    """Scaffolds a complete 2D project with HTML5 canvas and dynamic content-aware shots.

    Returns:
        (theme_name, palette_id, scene_sequence)
    """
    proj_dir.mkdir(parents=True, exist_ok=True)

    theme_name = detect_topic_theme(topic, lines)
    palette = pick_variation_palette(theme_name, recent_palette_ids)

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
    for tool_file in ["capture.mjs", "mix.py"]:
        src = inside_out_example / "tools" / tool_file
        if src.exists():
            shutil.copy2(src, tools_dir / tool_file)

    # Scaffolding source directory
    src_dir = proj_dir / "src"
    src_dir.mkdir(exist_ok=True)
    core_dir = src_dir / "core"
    core_dir.mkdir(exist_ok=True)

    # Copy core library helpers
    for core_file in ["lib.js", "timing.js", "captions.js"]:
        src = inside_out_example / "src" / "core" / core_file
        if src.exists():
            shutil.copy2(src, core_dir / core_file)

    # Write kit2d.js
    kit2d_code = generate_kit2d_js(palette)
    (core_dir / "kit2d.js").write_text(kit2d_code, encoding="utf-8")

    # Write shots.js
    shots_code, scene_sequence, focal_vector = generate_shots_js(
        title=title,
        topic=topic,
        lines=lines,
        theme=theme_name,
        palette=palette
    )
    (src_dir / "shots.js").write_text(shots_code, encoding="utf-8")

    # Write main.js complying fully with window.OP contract expected by tools/capture.mjs
    bg_color = palette.get("bg", "#0B1120")
    main_code = f"""// Boot: fonts -> script + timing -> captions -> shots. Then draw(t) renders film time t (pure function of t).
// window.OP is the API tools/capture.mjs drives: ready, bootError, duration(), draw(t), frame(t, q), cues(), shots().
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
  ctx.fillStyle = '{bg_color}'; ctx.fillRect(0, 0, W, H);
  const S = OP._shots; let i = S.length - 1; while (i > 0 && S[i].at > t) i--;
  const sh = S[i], end = i < S.length - 1 ? S[i + 1].at : T.dur, d = end - sh.at, lt = t - sh.at;
  // camera: punch-in on the cut + a slow push across the shot ("camera always moving")
  const punch = 1 + 0.13 * (1 - eo(clamp(lt / 0.32)));
  const drift = 1 + (sh.zoom ?? 0.06) * eio(clamp(lt / d));
  const [cx, cy] = sh.cam || [540, 900];
  ctx.save(); ctx.translate(cx, cy); ctx.scale(punch * drift, punch * drift); ctx.translate(-cx, -cy);
  sh.draw(lt, d, t);
  ctx.restore();
  ctx.globalAlpha = 1; ctx.letterSpacing = '0px';
  if (i > 0 && lt < 0.12) {{ ctx.fillStyle = '#FFFFFF'; ctx.globalAlpha = 0.55 * (1 - lt / 0.12); ctx.fillRect(0, 0, W, H); ctx.globalAlpha = 1; }}
  // fade from / to black on the first and last 0.25 s
  const fade = Math.min(clamp(t / 0.25), clamp((T.dur - t) / 0.35));
  if (fade < 1) {{ ctx.fillStyle = '#000'; ctx.globalAlpha = 1 - fade; ctx.fillRect(0, 0, W, H); ctx.globalAlpha = 1; }}
  drawCaption(t);
}}

(async () => {{
  try {{
    await document.fonts.load('900 100px Inter');
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
    // preview mode (not capture): play in real time, ?t=12.3 to hold a frame
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
    (src_dir / "main.js").write_text(main_code, encoding="utf-8")

    # Write index.html matching tools/capture.mjs expectations
    html_code = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{title}</title>
<style>
@font-face {{ font-family: 'Inter'; font-weight: 900; src: url('fonts/Inter-Black.otf') format('opentype'); }}
html, body {{ margin: 0; background: {bg_color}; height: 100%; }}
body {{ display: flex; align-items: center; justify-content: center; }}
canvas {{ display: block; height: 100vh; width: auto; max-width: 100vw; object-fit: contain; }}
body.capture canvas {{ height: auto; width: auto; }}
#play {{ position: fixed; font: 900 28px Inter, sans-serif; padding: 18px 36px; border: 0; border-radius: 40px; background: #FFD43B; color: #1A1A1E; cursor: pointer; }}
</style></head>
<body>
<canvas id="cv" width="1080" height="1920"></canvas>
<button id="play" hidden>▶ PLAY</button>
<script>if (location.search.includes('capture')) document.body.className = 'capture';</script>
<script type="module" src="src/main.js"></script>
</body></html>
"""
    (proj_dir / "index.html").write_text(html_code, encoding="utf-8")

    return theme_name, palette["id"], scene_sequence


def evaluate_visual_uniqueness(
    theme_name: str,
    palette_id: str,
    scene_sequence: List[str],
    history_entries: List[Dict[str, Any]]
) -> Tuple[bool, str]:
    """Gate 3 Pre-Render Visual Diversity Check.
    Verifies that planned visual presentation avoids consecutive stagnation.
    """
    if not history_entries:
        return True, f"Visual composition approved for initial video ({theme_name}, {palette_id})."

    # Check immediate predecessor
    last_entry = history_entries[-1]
    if (
        last_entry.get("theme") == theme_name and
        last_entry.get("palette") == palette_id and
        last_entry.get("scene_sequence") == scene_sequence
    ):
        return False, f"Visual stagnation: Planned video matches immediate predecessor theme ({theme_name}), palette ({palette_id}), and scene sequence."

    return True, f"Visual composition approved ({theme_name}, {palette_id})."

