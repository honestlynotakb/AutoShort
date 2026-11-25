#!/usr/bin/env python3
"""High-Quality 2D Animated Visual & Audio Generation Engine.

Generates fresh, topic-specific, non-repeating 2D motion graphics and audio mix assets
for every video. Eliminates hardcoded template cards, enforces caption-safe coordinates
(y = 200..1180 clear of y = 1250..1550 captions), synchronizes visual beats with Whisper
word timestamps via Wd(), and builds an auditable asset_manifest.json per run.
"""
from __future__ import annotations

import os
import re
import sys
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

ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT / "faceless-shorts"
if not SKILL_DIR.exists():
    SKILL_DIR = ROOT / ".agent" / "skills" / "faceless-shorts"


# ═════════════════════════════════════════════════════════════════════════════
# 1. DYNAMIC COLOR PALETTES & THEMES (Dark + Light Editorial / Parchment)
# ═════════════════════════════════════════════════════════════════════════════

THEMES: Dict[str, Dict[str, Any]] = {
    "COSMIC_SPACE": {
        "keywords": [
            "black hole", "gravity", "singularity", "outer space", "deep space",
            "in space", "spacesuit", "astronaut", "astronomy", "star", "starquake",
            "planet", "rogue planet", "exoplanet", "orbit", "orbital", "event horizon",
            "spaghettification", "time dilation", "universe", "magnetar", "pulsar",
            "nebula", "roche", "moon", "lunar", "sun", "solar", "mars", "martian",
            "venus", "neptune", "uranus", "galaxy", "milky way", "supernova",
            "wow! signal", "radio telescope", "telescope", "voyager", "satellite",
            "satellites", "starlink", "darksat", "kessler", "lagrange", "carrington",
            "armstrong limit", "bootes void", "sagittarius"
        ],
        "palettes": [
            {
                "id": "cosmic_abyss", "is_light": False,
                "bg": "#070913", "card": "#0F1424", "primary": "#00F0FF", "secondary": "#8B5CF6",
                "accent": "#FFD43B", "danger": "#EF4444", "ink": "#FFFFFF", "subtext": "#94A3B8",
                "on_primary": "#070913"
            },
            {
                "id": "solar_stellar", "is_light": False,
                "bg": "#0D0D11", "card": "#181820", "primary": "#F59E0B", "secondary": "#EF4444",
                "accent": "#38BDF8", "danger": "#DC2626", "ink": "#FFFFFF", "subtext": "#A1A1AA",
                "on_primary": "#0D0D11"
            },
            {
                "id": "nebula_violet", "is_light": False,
                "bg": "#110720", "card": "#1E0F38", "primary": "#A855F7", "secondary": "#EC4899",
                "accent": "#06B6D4", "danger": "#F43F5E", "ink": "#FFFFFF", "subtext": "#CBD5E1",
                "on_primary": "#FFFFFF"
            },
            {
                "id": "deep_aurora", "is_light": False,
                "bg": "#05131A", "card": "#0C232E", "primary": "#10B981", "secondary": "#06B6D4",
                "accent": "#FACC15", "danger": "#E11D48", "ink": "#FFFFFF", "subtext": "#94A3B8",
                "on_primary": "#05131A"
            },
            {
                "id": "observatory_ivory", "is_light": True,
                "bg": "#EEF3F8", "card": "#FFFFFF", "primary": "#1D4ED8", "secondary": "#0EA5E9",
                "accent": "#D97706", "danger": "#DC2626", "ink": "#0F172A", "subtext": "#475569",
                "on_primary": "#FFFFFF"
            },
        ]
    },
    "ATOMIC_PHYSICS": {
        "keywords": [
            "glass", "amorphous", "crystal", "atom", "atomic", "molecule",
            "molecular", "physics", "quantum", "matter", "lattice", "disordered",
            "prince rupert", "oobleck", "helium", "superfluid", "leidenfrost",
            "aerogel", "gallium", "cavitation", "shrimp", "ferrofluid", "mpemba",
            "triboluminescence", "invisibility", "cloak", "prism", "negative absolute",
            "nanoparticle", "non-newtonian", "viscosity", "electron"
        ],
        "palettes": [
            {
                "id": "quantum_matrix", "is_light": False,
                "bg": "#0B1120", "card": "#1E293B", "primary": "#10B981", "secondary": "#06B6D4",
                "accent": "#F59E0B", "danger": "#F43F5E", "ink": "#FFFFFF", "subtext": "#94A3B8",
                "on_primary": "#0B1120"
            },
            {
                "id": "editorial_ivory", "is_light": True,
                "bg": "#F4F1EA", "card": "#FFFFFF", "primary": "#0E7490", "secondary": "#2563EB",
                "accent": "#D97706", "danger": "#D62839", "ink": "#1A1A1E", "subtext": "#4B5563",
                "on_primary": "#FFFFFF"
            },
            {
                "id": "cryo_cyber", "is_light": False,
                "bg": "#08131E", "card": "#102336", "primary": "#38BDF8", "secondary": "#6366F1",
                "accent": "#FACC15", "danger": "#E11D48", "ink": "#FFFFFF", "subtext": "#94A3B8",
                "on_primary": "#08131E"
            },
            {
                "id": "neon_amber", "is_light": False,
                "bg": "#12100E", "card": "#241D18", "primary": "#F59E0B", "secondary": "#10B981",
                "accent": "#60A5FA", "danger": "#EF4444", "ink": "#FFFFFF", "subtext": "#D6D3D1",
                "on_primary": "#12100E"
            },
            {
                "id": "plasma_electric", "is_light": False,
                "bg": "#0C0A1E", "card": "#181438", "primary": "#8B5CF6", "secondary": "#3B82F6",
                "accent": "#10B981", "danger": "#EF4444", "ink": "#FFFFFF", "subtext": "#C7D2FE",
                "on_primary": "#FFFFFF"
            },
        ]
    },
    "SURVIVAL_TACTICAL": {
        "keywords": [
            "quicksand", "cold water", "cold shock", "survive", "survival",
            "escape", "elevator", "sinking car", "submerged", "rip current",
            "shoreline", "polar bear", "hypothermia", "undressing", "desert ants",
            "grain silo", "crowd crush", "avalanche", "air pocket", "step voltage",
            "step potential", "downed power", "carbon monoxide", "wet-bulb",
            "sweat", "evaporative cooling", "slot canyon", "flash flood",
            "implosion", "submersible", "lichtenberg", "lightning"
        ],
        "palettes": [
            {
                "id": "tactical_hazard", "is_light": False,
                "bg": "#18181B", "card": "#27272A", "primary": "#EAB308", "secondary": "#F97316",
                "accent": "#22C55E", "danger": "#EF4444", "ink": "#FFFFFF", "subtext": "#A1A1AA",
                "on_primary": "#18181B"
            },
            {
                "id": "field_manual_cream", "is_light": True,
                "bg": "#F5F2EB", "card": "#FFFFFF", "primary": "#B45309", "secondary": "#0F766E",
                "accent": "#15803D", "danger": "#DC2626", "ink": "#18181B", "subtext": "#52525B",
                "on_primary": "#FFFFFF"
            },
            {
                "id": "oceanic_abyss", "is_light": False,
                "bg": "#081C24", "card": "#0F3240", "primary": "#06B6D4", "secondary": "#3B82F6",
                "accent": "#F59E0B", "danger": "#EF4444", "ink": "#FFFFFF", "subtext": "#BAE6FD",
                "on_primary": "#081C24"
            },
            {
                "id": "arctic_frost", "is_light": False,
                "bg": "#0F172A", "card": "#1E293B", "primary": "#38BDF8", "secondary": "#94A3B8",
                "accent": "#F43F5E", "danger": "#DC2626", "ink": "#FFFFFF", "subtext": "#E2E8F0",
                "on_primary": "#0F172A"
            },
        ]
    },
    "HISTORIC_DOCUMENTARY": {
        "keywords": [
            "history", "ancient", "greek", "bronze", "brazen bull", "sicily",
            "flag", "purple", "tyrian", "snails", "mozambique", "nepal",
            "dancing plague", "1518", "strasbourg", "beer flood", "1814",
            "byford dolphin", "halifax", "1917", "mayan", "pyramid", "chichen itza",
            "molasses", "1919", "boston", "radium girls", "1920s", "lake nyos",
            "1986", "tambora", "1816", "chernobyl", "corium", "roman", "sapa",
            "qin shi huang", "emperor", "mercury", "1977"
        ],
        "palettes": [
            {
                "id": "parchment_atlas", "is_light": True,
                "bg": "#F2E8D5", "card": "#FBF7EE", "primary": "#9A3412", "secondary": "#B45309",
                "accent": "#0F766E", "danger": "#B91C1C", "ink": "#1C1917", "subtext": "#57534E",
                "on_primary": "#FFFFFF"
            },
            {
                "id": "bronze_antiquity", "is_light": False,
                "bg": "#17120E", "card": "#2C2017", "primary": "#D97706", "secondary": "#B45309",
                "accent": "#0D9488", "danger": "#B91C1C", "ink": "#FAF5F0", "subtext": "#D6D3D1",
                "on_primary": "#17120E"
            },
            {
                "id": "royal_purple", "is_light": False,
                "bg": "#140A1E", "card": "#28143C", "primary": "#A855F7", "secondary": "#EAB308",
                "accent": "#06B6D4", "danger": "#E11D48", "ink": "#FFFFFF", "subtext": "#E2E8F0",
                "on_primary": "#FFFFFF"
            },
            {
                "id": "vellum_manuscript", "is_light": False,
                "bg": "#221E1B", "card": "#332D29", "primary": "#E2D9C8", "secondary": "#CA8A04",
                "accent": "#14B8A6", "danger": "#DC2626", "ink": "#FFFFFF", "subtext": "#A8A29E",
                "on_primary": "#1C1917"
            },
        ]
    }
}

DEFAULT_PALETTE = {
    "id": "default_clean", "is_light": False,
    "bg": "#0F172A", "card": "#1E293B", "primary": "#38BDF8", "secondary": "#818CF8",
    "accent": "#FACC15", "danger": "#EF4444", "ink": "#FFFFFF", "subtext": "#94A3B8",
    "on_primary": "#0F172A"
}

MUSIC_ROOT_POOL = [196.0, 220.0, 246.9, 261.6, 293.7, 329.6]

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "because", "been", "before", "being",
    "between", "both", "but", "by", "can", "could", "did", "do", "does", "down",
    "during", "each", "even", "ever", "every", "for", "from", "had", "has", "have",
    "he", "her", "here", "his", "how", "if", "in", "inside", "into", "is", "it",
    "its", "just", "keep", "know", "like", "make", "more", "most", "much", "never",
    "no", "not", "now", "of", "off", "on", "once", "one", "only", "or", "other",
    "our", "out", "over", "right", "same", "see", "she", "should", "since", "so",
    "some", "still", "such", "than", "that", "the", "their", "them", "then", "there",
    "these", "they", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "way", "we", "were", "what", "when", "where", "which", "while",
    "who", "why", "will", "with", "within", "without", "would", "you", "your",
    "actually", "literally", "really", "happens", "happen", "happened", "thing",
    "time", "every", "single", "inch", "called", "known", "using", "making", "causing"
}


def has_keyword(text: str, keywords: List[str]) -> bool:
    """Checks if any keyword matches as a full word or defined subphrase."""
    for kw in keywords:
        if " " in kw:
            if re.search(r'\b' + re.escape(kw) + r'\b', text):
                return True
        else:
            if re.search(r'\b' + re.escape(kw) + r'\b', text):
                return True
    return False


def detect_topic_theme(topic: str, lines: List[Dict]) -> str:
    """Classifies topic and text into one of the 4 2D visual themes using weighted word-boundary matching."""
    topic_l = (topic or "").lower()
    body_l = " ".join(line.get("text", "") for line in lines).lower()
    best_theme = "ATOMIC_PHYSICS"
    max_score = 0

    for theme_name, theme_data in THEMES.items():
        score = 0
        for kw in theme_data["keywords"]:
            pat = r'\b' + re.escape(kw) + r'\b'
            if re.search(pat, topic_l):
                score += 3
            if re.search(pat, body_l):
                score += 1
        if score > max_score:
            max_score = score
            best_theme = theme_name
    return best_theme


def pick_variation_palette(
    theme_name: str,
    recent_palette_ids: List[str],
    variant_offset: int = 0
) -> Dict[str, Any]:
    """Selects a color palette not recently used, alternating dark and light modes for visual variety."""
    theme = THEMES.get(theme_name, THEMES["ATOMIC_PHYSICS"])
    palettes = theme["palettes"]
    available = [p for p in palettes if p["id"] not in recent_palette_ids]
    if available:
        return available[variant_offset % len(available)]
    return palettes[variant_offset % len(palettes)]


# ═════════════════════════════════════════════════════════════════════════════
# 2. CONTENT-AWARE FOCAL VECTOR ROUTER (24+ Subject Renderers)
# ═════════════════════════════════════════════════════════════════════════════

def detect_topic_focal_vector(topic: str, lines: List[Dict]) -> Tuple[str, str, str]:
    """Selects the primary procedural vector based on topic subject keywords.

    Returns:
        (vector_name, hook_draw_call, mechanism_draw_call)
    """
    text = (topic + " " + " ".join(l.get("text", "") for l in lines)).lower()

    # 1. Grain Silo Entrapment
    if has_keyword(text, ["grain silo", "flowing grain", "kernels", "auger"]):
        return (
            "GRAIN_SILO",
            "K.drawGrainSilo(540, 660, 520, 480, lt, clamp(seg(lt, 0.1, d * 0.8), 0.25, 0.9));",
            "K.drawGrainSilo(540, 620, 480, 440, lt * 1.3, 0.78);"
        )

    # 2. Crowd Crush Wave Dynamics
    if has_keyword(text, ["crowd crush", "crowd surge", "compressive asphyxiation", "square meter"]):
        return (
            "CROWD_SURGE",
            "K.drawCrowdWave(540, 660, 640, 440, lt);",
            "K.drawCrowdWave(540, 620, 620, 420, lt * 1.4);"
        )

    # 3. Avalanche Burial & Snow Layers
    if has_keyword(text, ["avalanche", "air pocket", "snow grains", "icy cast"]):
        return (
            "AVALANCHE_LAYERS",
            "K.drawAvalancheLayers(540, 660, 640, 440, lt);",
            "K.drawAvalancheLayers(540, 620, 620, 420, lt * 1.3);"
        )

    # 4. Radiation Core (Chernobyl / Radium) - checked BEFORE quicksand/sand
    if has_keyword(text, ["chernobyl", "corium", "elephant's foot", "roentgens", "radium", "alpha radiation", "radioactive"]):
        return (
            "RADIATION_CORE",
            "K.drawRadiationCore(540, 660, 210, lt);",
            "K.drawRadiationCore(540, 620, 190, lt * 1.4);"
        )

    # 5. Step Voltage / Electrical Ground Rings
    if has_keyword(text, ["step potential", "downed power", "fallen power line", "voltage rings", "energized"]):
        return (
            "STEP_VOLTAGE",
            "K.drawStepVoltage(540, 660, 600, 440, lt);",
            "K.drawStepVoltage(540, 620, 560, 420, lt * 1.3);"
        )

    # 6. Volcanic Plume & Climate Veil (Tambora 1816)
    if has_keyword(text, ["tambora", "volcanic eruption", "stratosphere", "sulfuric veil", "year without a summer"]):
        return (
            "VOLCANIC_PLUME",
            "K.drawVolcanoPlume(540, 660, 620, 450, lt);",
            "K.drawVolcanoPlume(540, 620, 580, 420, lt * 1.2);"
        )

    # 7. Suffocating Gas Cloud / Lake Nyos / Carbon Monoxide
    if has_keyword(text, ["lake nyos", "limnic", "carbon monoxide", "carboxyhemoglobin", "hemoglobin", "degassing"]):
        return (
            "GAS_VALLEY",
            "K.drawGasValley(540, 660, 640, 440, lt);",
            "K.drawGasValley(540, 620, 600, 420, lt * 1.3);"
        )

    # 8. Slot Canyon Flash Flood
    if has_keyword(text, ["slot canyon", "flash flood", "sandstone", "ravines", "mud and boulders"]):
        return (
            "CANYON_SURGE",
            "K.drawCanyonSurge(540, 660, 600, 440, lt);",
            "K.drawCanyonSurge(540, 620, 560, 420, lt * 1.3);"
        )

    # 9. Submersible Deep Sea Hull Implosion
    if has_keyword(text, ["implosion", "submersible", "titanium", "abyssal", "buckling"]):
        return (
            "SUBMERSIBLE_HULL",
            "K.drawSubmersibleHull(540, 660, 580, 380, lt);",
            "K.drawSubmersibleHull(540, 620, 540, 360, lt * 1.4);"
        )

    # 10. Diamond Rain on Ice Giants - checked BEFORE planetary orbit!
    if has_keyword(text, ["diamond rain", "diamond icebergs", "liquid carbon"]):
        return (
            "DIAMOND_RAIN",
            "K.drawDiamondRain(540, 660, 600, 460, lt);",
            "K.drawDiamondRain(540, 620, 560, 420, lt * 1.3);"
        )

    # 11. Thermal Gradient & Biological Shock (Cold Water, Lightning, Undressing, Wet-Bulb)
    if has_keyword(text, ["cold water", "cold shock", "hypothermia", "undressing", "lightning", "lichtenberg", "blood", "armstrong", "wet-bulb", "evaporative cooling"]):
        return (
            "THERMAL_GRADIENT",
            "K.drawThermalGradient(540, 660, 400, 400, seg(lt, 0, d), lt);",
            "K.drawThermalGradient(540, 620, 380, 360, 0.85, lt * 1.4);"
        )

    # 12. Black Hole / Gravitational Singularity
    if has_keyword(text, ["black hole", "singularity", "event horizon", "spaghettification", "spaghetti"]):
        return (
            "BLACK_HOLE",
            "K.drawBlackHole(540, 660, 175, lt);",
            "K.drawBlackHole(540, 620, 150, lt * 1.4, 0.5);"
        )

    # 13. Neutron Star / Magnetar / Boomerang / Wow Signal / Solar Flare
    if has_keyword(text, ["magnetar", "neutron star", "pulsar", "starquake", "magnetic field", "boomerang", "wow! signal", "radio burst", "carrington", "solar flare"]):
        return (
            "NEUTRON_STAR",
            "K.drawNeutronStar(540, 660, 130, lt, 1.15);",
            "K.drawNeutronStar(540, 620, 110, lt * 1.8, 1.35);"
        )

    # 14. Ocean Rip Currents, Flood Waves & Superhydrophobic Drops
    if has_keyword(text, ["rip current", "shoreline", "undertow", "swimmer", "swimming", "tsunami", "molasses", "beer flood", "porter", "lotus"]):
        return (
            "HYDRO_FLOW",
            "K.drawHydroFlow(540, 660, 580, 400, lt, 2.5);",
            "K.drawHydroFlow(540, 620, 540, 360, lt * 1.3, 3.0);"
        )

    # 15. Navigational Compass / Flags / Ants Navigation
    if has_keyword(text, ["flag", "nepal", "mozambique", "purple", "dye", "snails", "ant", "desert", "navigate", "navigation", "polarization", "dannebrog", "vatican"]):
        return (
            "TELEMETRY_COMPASS",
            "K.drawTelemetryCompass(540, 660, 190, lt * 0.4, lt);",
            "K.drawFlagEmblem(540, 620, 540, 360, lt);" if has_keyword(text, ["flag", "nepal", "mozambique", "purple", "dannebrog", "vatican"]) else "K.drawTelemetryCompass(540, 620, 170, lt * 0.6, lt);"
        )

    # 16. Submerged Vehicle / Elevator / Pressure Chamber
    if has_keyword(text, ["car", "elevator", "submerged", "door", "hydrostatic", "byford", "decompression", "faraday", "airliner"]):
        return (
            "SUBMERGED_CABIN",
            "K.drawSubmergedCabin(540, 660, 480, 360, lt, seg(lt, 0, d));",
            "K.drawSubmergedCabin(540, 620, 440, 320, lt, 0.85);"
        )

    # 17. Planetary Orbits / Satellites / Exoplanets / Roche Limit / Moon / Voyager
    if has_keyword(text, ["planet", "orbit", "solar system", "roche", "sun", "moon", "lunar", "great attractor", "milky way", "neptune", "uranus", "satellite", "satellites", "starlink", "darksat", "kessler", "lagrange", "venus", "mars", "voyager", "bootes", "55 cancri"]):
        return (
            "PLANETARY_ORBIT",
            "K.drawPlanetaryOrbit(540, 660, 220, lt, 4);",
            "K.drawPlanetaryOrbit(540, 620, 200, lt * 1.3, 3);"
        )

    # 18. Asteroid Shards / Halifax Explosion / Cosmic Dust
    if has_keyword(text, ["asteroid", "dust", "meteor", "halifax", "explosion", "blast", "kilotons", "sagittarius"]):
        return (
            "ASTEROID_FIELD",
            "K.drawAsteroidField(540, 660, 560, 420, lt, 35);",
            "K.drawAsteroidField(540, 620, 520, 380, lt * 1.4, 45);"
        )

    # 19. Molecular Brownian Simulation (checked BEFORE atomic lattice so "glass beakers" in Superfluid Helium doesn't misroute)
    if has_keyword(text, ["helium", "superfluid", "nitrogen", "leidenfrost", "mpemba", "aerogel", "temperature", "kelvin", "boil", "gallium", "ferrofluid", "negative kelvin", "superconductor", "meissner", "nitinol", "casimir", "bitumen", "tardigrade", "gecko"]):
        return (
            "MOLECULAR_SIM",
            "K.drawMolecularSimulation(540, 660, 220, lt, 1.5);",
            "K.drawMolecularSimulation(540, 620, 200, lt * 1.4, 2.0);"
        )

    # 20. Atomic Lattice & Molecular Crystals
    if has_keyword(text, ["glass", "crystal", "amorphous", "solid", "rupert", "lattice", "bismuth", "quartz", "piezoelectric"]):
        return (
            "ATOMIC_LATTICE",
            "K.drawAtomicLattice(540, 660, 500, 460, lt, eio(seg(lt, 0.2, 1.2)));",
            "K.drawAtomicLattice(540, 620, 460, 420, lt, 1.0);"
        )

    # 21. Prism Refraction & Optical Cloaking & Double-Slit
    if has_keyword(text, ["prism", "light", "optic", "cloak", "tape", "triboluminescence", "invisibility", "tunneling", "double-slit", "electrons"]):
        return (
            "PRISM_REFRACTION",
            "K.drawPrismRefraction(540, 660, 175, lt);",
            "K.drawPrismRefraction(540, 620, 155, lt * 1.2);"
        )

    # 22. Quicksand Vortex / Non-Newtonian Oobleck / Chain Fountain
    if has_keyword(text, ["quicksand", "oobleck", "non-newtonian", "cycloid", "brachistochrone", "chain fountain", "mould effect"]):
        return (
            "QUICKSAND_VORTEX",
            "K.drawQuicksandVortex(540, 660, 225, lt, seg(lt, 0, d));",
            "K.drawQuicksandVortex(540, 620, 205, lt, 0.8);"
        )

    # 23. Acoustic Wave Chamber (Brazen Bull / Mayan Pyramids / Chladni / Flutter)
    if has_keyword(text, ["brazen bull", "acoustic", "pyramid", "mayan", "echo", "sound", "chirp", "silence", "supernova", "chladni", "flutter", "tacoma"]):
        return (
            "ACOUSTIC_RESONATOR",
            "K.drawAcousticResonator(540, 660, 1.2, lt, 1.0);",
            "K.drawAcousticResonator(540, 620, 1.15, lt, 1.2);"
        )

    # 24. Historic Archive Map (Roman Sapa, Qin Shi Huang, Dancing Plague, Polar Bear)
    if has_keyword(text, ["roman", "sapa", "qin shi", "mercury", "dancing plague", "strasbourg", "polar bear", "vitamin a"]):
        return (
            "ARCHIVE_MAP",
            "K.drawArchiveMap(540, 660, 580, 420, lt);",
            "K.drawArchiveMap(540, 620, 540, 380, lt * 1.2);"
        )

    # Default clean crystal/diagram vector (no hardcoded dummy cards)
    return (
        "ATOMIC_LATTICE",
        "K.drawAtomicLattice(540, 660, 480, 420, lt, 0.4);",
        "K.drawAtomicLattice(540, 620, 440, 380, lt, 0.8);"
    )


def _vector_draw_call(vector_name: str, is_hook: bool = True) -> str:
    """Maps any vector archetype name to its Canvas 2D draw invocation positioned in safe zone y=400..880."""
    y = 660 if is_hook else 620
    mapping = {
        "GRAIN_SILO": f"K.drawGrainSilo(540, {y}, 520, 440, lt, {'clamp(seg(lt, 0.1, d * 0.85), 0.25, 0.9)' if is_hook else '0.78'});",
        "CROWD_SURGE": f"K.drawCrowdWave(540, {y}, 620, 420, lt * {'1.0' if is_hook else '1.35'});",
        "AVALANCHE_LAYERS": f"K.drawAvalancheLayers(540, {y}, 620, 420, lt * {'1.0' if is_hook else '1.25'});",
        "RADIATION_CORE": f"K.drawRadiationCore(540, {y}, {205 if is_hook else 185}, lt * {'1.0' if is_hook else '1.35'});",
        "STEP_VOLTAGE": f"K.drawStepVoltage(540, {y}, 580, 420, lt * {'1.0' if is_hook else '1.3'});",
        "VOLCANIC_PLUME": f"K.drawVolcanoPlume(540, {y}, 600, 430, lt * {'1.0' if is_hook else '1.25'});",
        "GAS_VALLEY": f"K.drawGasValley(540, {y}, 620, 420, lt * {'1.0' if is_hook else '1.3'});",
        "CANYON_SURGE": f"K.drawCanyonSurge(540, {y}, 580, 420, lt * {'1.0' if is_hook else '1.3'});",
        "SUBMERSIBLE_HULL": f"K.drawSubmersibleHull(540, {y}, 560, 360, lt * {'1.0' if is_hook else '1.35'});",
        "DIAMOND_RAIN": f"K.drawDiamondRain(540, {y}, 580, 430, lt * {'1.0' if is_hook else '1.3'});",
        "THERMAL_GRADIENT": f"K.drawThermalGradient(540, {y}, 390, 370, {'seg(lt, 0, d)' if is_hook else '0.85'}, lt * {'1.0' if is_hook else '1.4'});",
        "BLACK_HOLE": f"K.drawBlackHole(540, {y}, {175 if is_hook else 150}, lt * {'1.0' if is_hook else '1.4'}, {0 if is_hook else 0.5});",
        "NEUTRON_STAR": f"K.drawNeutronStar(540, {y}, {130 if is_hook else 110}, lt * {'1.0' if is_hook else '1.7'}, {1.15 if is_hook else 1.35});",
        "HYDRO_FLOW": f"K.drawHydroFlow(540, {y}, 560, 380, lt * {'1.0' if is_hook else '1.3'}, {2.5 if is_hook else 3.0});",
        "TELEMETRY_COMPASS": f"K.drawTelemetryCompass(540, {y}, {185 if is_hook else 165}, lt * {'0.4' if is_hook else '0.65'}, lt);",
        "FLAG_EMBLEM": f"K.drawFlagEmblem(540, {y}, 540, 360, lt);",
        "SUBMERGED_CABIN": f"K.drawSubmergedCabin(540, {y}, 470, 340, lt, {'seg(lt, 0, d)' if is_hook else '0.85'});",
        "PLANETARY_ORBIT": f"K.drawPlanetaryOrbit(540, {y}, {220 if is_hook else 195}, lt * {'1.0' if is_hook else '1.3'}, {4 if is_hook else 3});",
        "ASTEROID_FIELD": f"K.drawAsteroidField(540, {y}, 550, 400, lt * {'1.0' if is_hook else '1.4'}, {35 if is_hook else 45});",
        "ATOMIC_LATTICE": f"K.drawAtomicLattice(540, {y}, 480, 420, lt, {'eio(seg(lt, 0.2, 1.2))' if is_hook else '1.0'});",
        "MOLECULAR_SIM": f"K.drawMolecularSimulation(540, {y}, {215 if is_hook else 195}, lt * {'1.0' if is_hook else '1.4'}, {1.5 if is_hook else 2.0});",
        "PRISM_REFRACTION": f"K.drawPrismRefraction(540, {y}, {175 if is_hook else 155}, lt * {'1.0' if is_hook else '1.25'});",
        "QUICKSAND_VORTEX": f"K.drawQuicksandVortex(540, {y}, {215 if is_hook else 195}, lt, {'seg(lt, 0, d)' if is_hook else '0.82'});",
        "ACOUSTIC_RESONATOR": f"K.drawAcousticResonator(540, {y}, {1.2 if is_hook else 1.1}, lt, {1.0 if is_hook else 1.2});",
        "ARCHIVE_MAP": f"K.drawArchiveMap(540, {y}, 560, 400, lt * {'1.0' if is_hook else '1.2'});",
    }
    return mapping.get(vector_name, mapping["ATOMIC_LATTICE"])


# ═════════════════════════════════════════════════════════════════════════════
# 3. SCRIPT-DRIVEN VISUAL BEAT COMPOSER (Zero Boilerplate)
# ═════════════════════════════════════════════════════════════════════════════

_NUMBER_UNIT_RE = re.compile(
    r'\b(\d+(?:[.,]\d+)?)\s*(percent|%|degrees?|kelvin|fahrenheit|celsius|mph|miles per hour|'
    r'feet per second|ft/s|seconds?|minutes?|hours?|days?|years?|gallons?|pounds?|lbs?|psi|'
    r'tons?|kilotons?|roentgens?|volts?|times|atmospheres?|meters?|feet|inches|grams?|ounce|'
    r'square meter|million|billion|thousand|hundred)\b',
    re.IGNORECASE
)

_WRITTEN_NUMBERS = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
    "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
    "fifteen": "15", "twenty": "20", "thirty": "30", "forty": "40", "fifty": "50",
    "sixty": "60", "seventy": "70", "eighty": "80", "ninety": "90",
    "hundred": "100", "thousand": "1,000", "million": "1M", "billion": "1B"
}

_WRITTEN_UNIT_RE = re.compile(
    r'\b(zero|one|two|three|four|five|six|seven|eight|nine|ten|fifteen|twenty|thirty|'
    r'forty|fifty|sixty|seventy|eighty|ninety|nine hundred|eight thousand|ten thousand|'
    r'sixty-three thousand|two hundred|three hundred|four hundred|five thousand|'
    r'six thousand|thirty-five|ninety-five|ninety-eight|ninety-nine)\s+'
    r'(percent|degrees?|kelvin|seconds?|minutes?|hours?|days?|years?|gallons?|pounds?|'
    r'miles per hour|feet per second|tons?|kilotons?|roentgens?|volts?|times|atmospheres?|'
    r'feet|snails|gram|ounce|people|buildings|million|billion)\b',
    re.IGNORECASE
)


_DANGLING_TAIL = {"a", "an", "the", "in", "on", "of", "for", "to", "and", "or", "with", "by", "at", "into", "from", "as", "is", "are"}


def _clean_short_phrase(text: str, max_len: int = 24) -> str:
    clean = re.sub(r'[*|]+', ' ', str(text or '')).strip()
    clean = re.sub(r'[?!.,;:"\']+', '', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    words = clean.split()
    if len(clean) > max_len:
        out = []
        for w in words:
            candidate = " ".join(out + [w])
            if len(candidate) > max_len:
                break
            out.append(w)
        words = out if out else [clean[:max_len]]
    while len(words) > 1 and words[-1].lower() in _DANGLING_TAIL:
        words.pop()
    return (" ".join(words) if words else clean[:max_len]).upper()


def _extract_focus_word(line: Dict[str, Any]) -> str:
    """Selects a real spoken keyword from line['text'] for Whisper Wd() synchronization."""
    text = str(line.get("text", ""))
    caps = str(line.get("caps", ""))
    text_tokens = [re.sub(r'[^a-z0-9]+', '', w.lower()) for w in text.split()]
    text_tokens = [t for t in text_tokens if len(t) >= 3]

    # Prefer the starred *word from caps if it actually exists in spoken text
    starred = re.findall(r'\*([A-Za-z0-9\'-]+)', caps)
    for sw in starred:
        norm_sw = re.sub(r'[^a-z0-9]+', '', sw.lower())
        if len(norm_sw) >= 3 and any(tok.startswith(norm_sw) or norm_sw.startswith(tok) for tok in text_tokens):
            return norm_sw

    # Otherwise pick the longest informative word from line text
    content = [t for t in text_tokens if t not in STOP_WORDS]
    if content:
        return max(content, key=len)
    return text_tokens[-1] if text_tokens else ""


def _extract_line_pill(line: Dict[str, Any], used_pills: set, fallback_anchor: str) -> str:
    """Derives a concise, unique 2-3 word badge directly from the line's caps or narration."""
    caps = str(line.get("caps", ""))
    text = str(line.get("text", ""))

    candidates: List[str] = []
    if caps:
        raw_chunks = [ch.strip() for ch in caps.split('|') if ch.strip()]
        # Prioritize chunks containing a *highlighted keyword over setup fragments
        prioritized = sorted(raw_chunks, key=lambda ch: (0 if '*' in ch else 1))
        for ch in prioritized:
            cand = _clean_short_phrase(re.sub(r'\*+', '', ch), 26)
            if cand and len(cand) >= 4:
                candidates.append(cand)

    # Extract 2-3 consecutive informative words from line text
    words = [re.sub(r'[^A-Za-z0-9-]+', '', w) for w in text.split()]
    content_words = [w for w in words if len(w) >= 3 and w.lower() not in STOP_WORDS]
    if len(content_words) >= 2:
        candidates.append(_clean_short_phrase(" ".join(content_words[:3]), 26))
        candidates.append(_clean_short_phrase(" ".join(content_words[-2:]), 26))
    elif content_words:
        candidates.append(_clean_short_phrase(content_words[0], 26))

    if fallback_anchor:
        candidates.append(_clean_short_phrase(fallback_anchor, 26))

    for cand in candidates:
        norm = normalize_card_text(cand)
        ok, _ = check_boilerplate_cards([cand], topic=fallback_anchor, script_text=text)
        if ok and norm and norm not in used_pills:
            used_pills.add(norm)
            return cand

    # Guaranteed unique fallback based on first/last content words
    unique_label = _clean_short_phrase(
        f"{content_words[0]} {content_words[-1]}" if len(content_words) >= 2 else f"{fallback_anchor[:16]} {len(used_pills)+1}",
        26
    )
    used_pills.add(normalize_card_text(unique_label))
    return unique_label


def _extract_stat_from_line(line_text: str, topic_anchor: str) -> Tuple[str, str]:
    """Extracts a real numeric measurement or key quantitative label from the spoken line."""
    m = _NUMBER_UNIT_RE.search(line_text)
    if m:
        val = f"{m.group(1)} {m.group(2)}".upper()
        words = [re.sub(r'[^A-Za-z0-9-]+', '', w) for w in line_text.split()]
        desc = [w for w in words if len(w) >= 4 and w.lower() not in STOP_WORDS and m.group(1).lower() not in w.lower()]
        lbl = _clean_short_phrase(" ".join(desc[:3]) or topic_anchor, 32)
        return _clean_short_phrase(val, 12), lbl

    wm = _WRITTEN_UNIT_RE.search(line_text)
    if wm:
        raw_num = wm.group(1).lower().replace('-', ' ')
        unit = wm.group(2).upper()
        compact_num = _WRITTEN_NUMBERS.get(raw_num, raw_num.upper())
        if "nine hundred" in raw_num:
            compact_num = "900"
        elif "eight thousand" in raw_num:
            compact_num = "8,000"
        elif "ten thousand" in raw_num:
            compact_num = "10,000"
        elif "sixty-three thousand" in wm.group(1).lower():
            compact_num = "63,000"
        elif "six thousand" in raw_num:
            compact_num = "6,000"
        elif "three hundred" in raw_num:
            compact_num = "300"
        elif "four hundred" in raw_num:
            compact_num = "400"
        elif "two hundred" in raw_num:
            compact_num = "200"
        elif "thirty five" in raw_num:
            compact_num = "35"
        elif "ninety five" in raw_num:
            compact_num = "95"
        val = f"{compact_num} {unit[:8]}".strip()
        words = [re.sub(r'[^A-Za-z0-9-]+', '', w) for w in line_text.split()]
        desc = [w for w in words if len(w) >= 4 and w.lower() not in STOP_WORDS and w.lower() not in wm.group(0).lower()]
        lbl = _clean_short_phrase(" ".join(desc[:3]) or topic_anchor, 32)
        return _clean_short_phrase(val, 14), lbl

    # Fallback: crisp 1-2 word focal concept from the line itself (never fake numbers)
    words = [re.sub(r'[^A-Za-z0-9-]+', '', w) for w in line_text.split()]
    content = [w for w in words if len(w) >= 4 and w.lower() not in STOP_WORDS]
    big = _clean_short_phrase(content[0] if content else topic_anchor, 13)
    sub = _clean_short_phrase(" ".join(content[1:4]) if len(content) > 1 else topic_anchor, 32)
    return big, sub


def _extract_split_from_line(line_text: str, topic_anchor: str) -> Tuple[str, str, str, str]:
    """Builds a topic-specific left-vs-right contrast strictly from the line's clauses."""
    lower = line_text.lower()
    words = [re.sub(r'[^A-Za-z0-9-]+', '', w) for w in line_text.split()]
    content = [w for w in words if len(w) >= 3 and w.lower() not in STOP_WORDS]

    if any(k in lower for k in ["instead", "but", "however", "rather", "not"]):
        parts = re.split(r'\b(?:instead|but|however|rather than)\b|[:;,]', line_text, maxsplit=1, flags=re.IGNORECASE)
        if len(parts) == 2 and parts[0].strip() and parts[1].strip():
            left_title = _clean_short_phrase(" ".join(w for w in parts[0].split() if w.lower() not in STOP_WORDS)[:28], 18)
            right_title = _clean_short_phrase(" ".join(w for w in parts[1].split() if w.lower() not in STOP_WORDS)[:28], 18)
            if left_title and right_title and left_title != right_title:
                return ("AVOID / MYTH", left_title, "REAL MECHANISM", right_title)

    mid = max(1, len(content) // 2)
    left_title = _clean_short_phrase(" ".join(content[:2]) or topic_anchor, 18)
    right_title = _clean_short_phrase(" ".join(content[mid:mid + 2]) or content[-1] if content else topic_anchor, 18)
    if left_title == right_title:
        right_title = _clean_short_phrase(" ".join(content[-2:]) or "OUTCOME", 18)
    return ("CAUSE", left_title, "EFFECT", right_title)


def _extract_pipeline_stages(lines: List[Dict], topic_anchor: str) -> List[str]:
    """Extracts 3 distinct chronological stage labels from the video's beginning, middle, and twist."""
    n = len(lines)
    pick_indices = [1 if n > 2 else 0, max(0, n // 2), max(0, n - 2)]
    stages: List[str] = []
    for idx in pick_indices:
        txt = str(lines[idx].get("text", ""))
        words = [re.sub(r'[^A-Za-z0-9-]+', '', w) for w in txt.split()]
        content = [w for w in words if len(w) >= 4 and w.lower() not in STOP_WORDS]
        label = _clean_short_phrase(" ".join(content[:2]) if content else f"{topic_anchor} {len(stages)+1}", 14)
        if label in stages:
            label = _clean_short_phrase(" ".join(content[-2:]) if len(content) >= 2 else f"PHASE {len(stages)+1}", 14)
        stages.append(label)
    return stages


def _select_sfx_cue(line_text: str, card_kind: str, is_first: bool, is_last: bool) -> str:
    """Matches sound effect cue type to the physical action in the line."""
    t = line_text.lower()
    if is_first:
        return "pop"
    if is_last:
        return "slam"
    if any(k in t for k in ["bubble", "boil", "liquid", "water", "flood", "molasses", "ocean", "sea"]):
        return "bubbles"
    if any(k in t for k in ["acid", "burn", "heat", "hot", "flame", "fire", "melt", "vapor"]):
        return "sizzle"
    if any(k in t for k in ["glow", "light", "diamond", "spark", "prism", "star", "blue"]):
        return "sparkle"
    if any(k in t for k in ["alarm", "fatal", "kill", "dead", "danger", "radiation", "collapse", "explode", "blast"]):
        return "alarm"
    if any(k in t for k in ["seconds", "minutes", "years", "millisecond", "191", "181", "151", "198", "192"]):
        return "tock"
    if any(k in t for k in ["heart", "breath", "exhale", "lungs", "blood", "gasp"]):
        return "heartbeat"
    if any(k in t for k in ["sink", "fall", "drop", "plunge", "bury"]):
        return "plop"
    if any(k in t for k in ["slide", "flow", "wave", "drift", "rush", "race"]):
        return "slide"
    if any(k in t for k in ["myth", "never", "impossible", "shatter", "snap", "crush"]):
        return "slam"
    if card_kind in ("BIG_STAT_METRIC", "PIPELINE_FLOW", "COMPARE_SPLIT"):
        return "pop"
    return "thud"


def compose_video_visual_plan(
    title: str,
    topic: str,
    lines: List[Dict],
    theme: str,
    asset_seed: str = "",
    visual_plan: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Creates a per-line, zero-boilerplate storyboard plan with diverse layouts and backgrounds."""
    clean_title = re.sub(r'#shorts', '', title, flags=re.IGNORECASE).strip()
    vector_name, _, _ = detect_topic_focal_vector(topic, lines)
    topic_anchor = _clean_short_phrase(clean_title or topic, 22)

    bg_pool = ["STARFIELD", "HEX", "CONTOURS", "RADAR", "BLUEPRINT", "WAVEMESH"]
    seed_int = int(hashlib.sha256((asset_seed or topic).encode("utf-8")).hexdigest()[:8], 16)
    bg_offset = seed_int % len(bg_pool)

    # Theme-preferred widget guarantees Tier 8 theme diversity while varying every shot's content
    theme_required_kind = {
        "SURVIVAL_TACTICAL": "COMPARE_SPLIT",
        "COSMIC_SPACE": "BIG_STAT_METRIC",
        "ATOMIC_PHYSICS": "WAVE_OSCILLATION",
        "HISTORIC_DOCUMENTARY": "PIPELINE_FLOW",
    }.get(theme, "BIG_STAT_METRIC")

    middle_rotation = [
        "HERO_MECHANISM",
        theme_required_kind,
        "FACT_GAUGE",
        "IMPACT_STAMP",
        "CALLOUT_DIAGRAM",
        "COMPARISON_BAR",
    ]
    # Rotate starting offset by seed and guarantee theme_required_kind is at middle index 1 (line 2) with zero duplicates
    if len(lines) > 3:
        rot = seed_int % len(middle_rotation)
        rotated = middle_rotation[rot:] + middle_rotation[:rot]
        if theme_required_kind in rotated:
            rotated.remove(theme_required_kind)
            rotated.insert(1, theme_required_kind)
        middle_rotation = rotated

    used_pills: set = set()
    pipeline_stages = _extract_pipeline_stages(lines, topic_anchor)
    shots_spec: List[Dict[str, Any]] = []
    card_texts: List[str] = []
    scene_sequence: List[str] = []
    background_sequence: List[str] = []

    num_lines = len(lines)
    for i, line in enumerate(lines):
        line_text = str(line.get("text", ""))
        custom_vis = line.get("visual") if isinstance(line.get("visual"), dict) else None
        if not custom_vis and visual_plan and i < len(visual_plan) and isinstance(visual_plan[i], dict):
            custom_vis = visual_plan[i]

        focus_word = (custom_vis.get("focus_word") if custom_vis else None) or _extract_focus_word(line)
        pill = ""
        if custom_vis and custom_vis.get("pill"):
            cand_pill = _clean_short_phrase(custom_vis["pill"], 24)
            ok, _ = check_boilerplate_cards([cand_pill], topic=topic, title=clean_title, script_text=line_text)
            if ok and normalize_card_text(cand_pill) not in used_pills:
                pill = cand_pill
                used_pills.add(normalize_card_text(cand_pill))
        if not pill:
            pill = _extract_line_pill(line, used_pills, topic_anchor)

        bg_mode = bg_pool[(bg_offset + i) % len(bg_pool)]
        background_sequence.append(bg_mode)

        if i == 0:
            kind = f"HOOK_{vector_name}"
            stat_val, stat_lbl = _extract_stat_from_line(line_text, topic_anchor)
            hook_sub = _clean_short_phrase(stat_val if any(c.isdigit() for c in stat_val) else topic_anchor, 28)
            if normalize_card_text(hook_sub) == normalize_card_text(pill):
                hook_sub = _clean_short_phrase(line_text, 28)
            card_data = {"hook_callout": _clean_short_phrase(clean_title, 44), "hook_sub": hook_sub}
            card_texts.extend([pill, card_data["hook_callout"], hook_sub])
        elif i == num_lines - 1:
            kind = "LOOP_OUTRO"
            loop_label = _clean_short_phrase(clean_title, 44)
            takeaway = _clean_short_phrase(
                " ".join([w for w in re.sub(r'[^A-Za-z0-9 ]+', '', line_text).split() if w.lower() not in STOP_WORDS][:3]) or topic_anchor,
                26
            )
            if custom_vis and isinstance(custom_vis.get("card_data"), dict):
                takeaway = _clean_short_phrase(custom_vis["card_data"].get("takeaway", takeaway), 26)
            card_data = {"loop_label": loop_label, "takeaway": takeaway}
            card_texts.extend([pill, takeaway])
        else:
            slot_kind = middle_rotation[(i - 1) % len(middle_rotation)]

            if slot_kind == "HERO_MECHANISM":
                kind = f"MECH_{vector_name}"
                val, lbl = _extract_stat_from_line(line_text, topic_anchor)
                card_data = {"pointer_label": _clean_short_phrase(lbl, 22), "metric_val": val}
                card_texts.extend([pill, card_data["pointer_label"]])
            elif slot_kind == "COMPARE_SPLIT":
                kind = "COMPARE_SPLIT"
                la, ta, lb, tb = _extract_split_from_line(line_text, topic_anchor)
                if custom_vis and isinstance(custom_vis.get("card_data"), dict):
                    cd = custom_vis["card_data"]
                    la = _clean_short_phrase(cd.get("label_a", la), 16)
                    ta = _clean_short_phrase(cd.get("title_a", ta), 18)
                    lb = _clean_short_phrase(cd.get("label_b", lb), 16)
                    tb = _clean_short_phrase(cd.get("title_b", tb), 18)
                card_data = {"label_a": la, "title_a": ta, "label_b": lb, "title_b": tb}
                card_texts.extend([pill, la, ta, lb, tb])
            elif slot_kind == "BIG_STAT_METRIC":
                kind = "BIG_STAT_METRIC"
                val, lbl = _extract_stat_from_line(line_text, topic_anchor)
                if custom_vis and isinstance(custom_vis.get("card_data"), dict):
                    val = _clean_short_phrase(custom_vis["card_data"].get("value", val), 14)
                    lbl = _clean_short_phrase(custom_vis["card_data"].get("label", lbl), 30)
                card_data = {"value": val, "label": lbl}
                card_texts.extend([pill, val, lbl])
            elif slot_kind == "WAVE_OSCILLATION":
                kind = "WAVE_OSCILLATION"
                _, lbl = _extract_stat_from_line(line_text, topic_anchor)
                wave_title = _clean_short_phrase(f"{lbl} WAVE", 26)
                card_data = {"wave_label": wave_title, "sub_label": pill}
                card_texts.extend([pill, wave_title])
            elif slot_kind == "PIPELINE_FLOW":
                kind = "PIPELINE_FLOW"
                stages = list(pipeline_stages)
                if custom_vis and isinstance(custom_vis.get("card_data"), dict):
                    raw_stages = custom_vis["card_data"].get("stages")
                    if isinstance(raw_stages, list) and len(raw_stages) == 3:
                        stages = [_clean_short_phrase(s, 14) for s in raw_stages]
                card_data = {"stages": stages, "active": min(3, max(1, math.ceil((i / max(1, num_lines - 1)) * 3)))}
                card_texts.extend([pill] + stages)
            elif slot_kind == "FACT_GAUGE":
                kind = "METRIC_TELEMETRY"
                val, lbl = _extract_stat_from_line(line_text, topic_anchor)
                if custom_vis and isinstance(custom_vis.get("card_data"), dict):
                    val = _clean_short_phrase(custom_vis["card_data"].get("value", val), 14)
                    lbl = _clean_short_phrase(custom_vis["card_data"].get("label", lbl), 22)
                ratio = round(0.55 + ((i * 17 + seed_int) % 40) / 100.0, 2)
                card_data = {"value": val, "label": _clean_short_phrase(lbl, 22), "ratio": ratio}
                card_texts.extend([pill, card_data["value"], card_data["label"]])
            elif slot_kind == "IMPACT_STAMP":
                kind = "HAZARD_TWIST"
                danger_words = [
                    "myth", "never", "impossible", "kill", "kills", "fatal", "trap",
                    "die", "died", "crush", "freeze", "poison", "fail", "fails", "tear",
                    "deadly", "lethal", "suffocat", "drown", "burn", "risk", "burst",
                    "snap", "snapped", "collapse", "blind", "toxic"
                ]
                is_danger = any(w in line_text.lower() for w in danger_words)
                stamp = "x" if is_danger else "check"
                if custom_vis and custom_vis.get("stamp") in ("x", "check"):
                    stamp = custom_vis["stamp"]
                banner = pill
                if custom_vis and isinstance(custom_vis.get("card_data"), dict) and custom_vis["card_data"].get("banner"):
                    banner = _clean_short_phrase(custom_vis["card_data"]["banner"], 28)
                card_data = {"stamp": stamp, "banner": banner}
                card_texts.extend([pill, banner])
            elif slot_kind == "CALLOUT_DIAGRAM":
                kind = f"VECTOR_CALLOUT_{vector_name}"
                val, lbl = _extract_stat_from_line(line_text, topic_anchor)
                sub_lbl = pill
                if custom_vis and isinstance(custom_vis.get("card_data"), dict):
                    val = _clean_short_phrase(custom_vis["card_data"].get("value", val), 18)
                    sub_lbl = _clean_short_phrase(custom_vis["card_data"].get("label", sub_lbl), 28)
                card_data = {"pointer_label": _clean_short_phrase(val, 18), "sub_label": sub_lbl}
                card_texts.extend([pill, card_data["pointer_label"], card_data["sub_label"]])
            else:
                kind = "METRIC_COMPARISON"
                la, ta, lb, tb = _extract_split_from_line(line_text, topic_anchor)
                if custom_vis and isinstance(custom_vis.get("card_data"), dict):
                    cd = custom_vis["card_data"]
                    ta = _clean_short_phrase(cd.get("left", ta), 20)
                    tb = _clean_short_phrase(cd.get("right", tb), 20)
                card_data = {"left": ta, "right": tb, "ratio": round(0.62 + (i % 3) * 0.1, 2)}
                card_texts.extend([pill, ta, tb])

        scene_sequence.append(kind)
        sfx = _select_sfx_cue(line_text, kind, i == 0, i == num_lines - 1)
        sub_bg_mode = bg_pool[(bg_offset + i + 3) % len(bg_pool)]
        word_count = len(line_text.split())
        shots_spec.append({
            "index": i,
            "kind": kind,
            "vector": vector_name,
            "pill": pill,
            "focus_word": focus_word,
            "bg_mode": bg_mode,
            "sub_bg_mode": sub_bg_mode,
            "has_subcut": (0 < i < num_lines - 1) and (word_count >= 11),
            "word_count": word_count,
            "card_data": card_data,
            "sfx": sfx,
            "cam_zoom": round(0.08 + ((i + seed_int) % 4) * 0.04, 2),
            "cam_x": 540 + (((i % 3) - 1) * 28),
            "cam_y": 760 if i % 2 == 0 else 720,
        })

    # Deduplicate card_texts preserving order
    unique_cards = list(dict.fromkeys(c for c in card_texts if c))
    return {
        "vector_name": vector_name,
        "theme": theme,
        "topic_anchor": topic_anchor,
        "shots": shots_spec,
        "scene_sequence": scene_sequence,
        "background_sequence": background_sequence,
        "card_texts": unique_cards,
    }


# ═════════════════════════════════════════════════════════════════════════════
# 4. 2D PROCEDURAL KIT GENERATOR (src/core/kit2d.js)
# ═════════════════════════════════════════════════════════════════════════════

def generate_kit2d_js(palette: Dict[str, Any]) -> str:
    """Generates the procedural 2D canvas drawing kit tailored to the active color palette."""
    pal_with_defaults = dict(DEFAULT_PALETTE)
    pal_with_defaults.update(palette)
    pal_json = json.dumps(pal_with_defaults)

    return f"""// Procedural 2D Motion Graphics & Illustrated Vector Drawing Kit
import {{ ctx, W, H, TAU, lerp, clamp, seg, eo, eio, eob, rnd, rr, circle, ell, line }} from './lib.js';

export const P = {pal_json};

// ═══════════════════════ PARALLAX BACKGROUNDS ═══════════════════════

export function bgGrid(t, speed = 25) {{
  ctx.fillStyle = P.bg;
  ctx.fillRect(-300, -300, W + 600, H + 600);
  ctx.save();
  ctx.strokeStyle = P.primary + '1C';
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
    const alpha = 0.2 + rnd(i * 11) * 0.45;
    circle(x, y, r, color + Math.floor(alpha * 255).toString(16).padStart(2, '0'));
  }}
  ctx.restore();
}}

export function bgConcentricWaves(t, count = 5, color = P.secondary) {{
  ctx.save();
  for (let i = 0; i < count; i++) {{
    const rad = ((t * 40 + i * 200) % 1200);
    const alpha = clamp(1 - rad / 1200) * 0.22;
    ctx.beginPath();
    ctx.arc(W / 2, H / 2, rad, 0, TAU);
    ctx.strokeStyle = color + Math.floor(alpha * 255).toString(16).padStart(2, '0');
    ctx.lineWidth = 3;
    ctx.stroke();
  }}
  ctx.restore();
}}

/** Flowing Topographic & Oceanic Depth Contour Lines */
export function bgContours(t, count = 7, color = P.secondary) {{
  ctx.fillStyle = P.bg;
  ctx.fillRect(-300, -300, W + 600, H + 600);
  ctx.save();
  ctx.lineWidth = 3;
  for (let i = 0; i < count; i++) {{
    const yBase = (H / (count + 1)) * (i + 1);
    const alpha = 0.1 + (i % 3) * 0.05;
    ctx.strokeStyle = color + Math.floor(alpha * 255).toString(16).padStart(2, '0');
    ctx.beginPath();
    ctx.moveTo(0, yBase);
    for (let x = 0; x <= W + 60; x += 60) {{
      const wave = Math.sin(x * 0.005 + t * 0.8 + i) * 45 + Math.cos(x * 0.01 - t * 0.5) * 25;
      ctx.lineTo(x, yBase + wave);
    }}
    ctx.stroke();
  }}
  ctx.restore();
}}

/** Hexagonal Technical Honeycomb Matrix */
export function bgHex(t, size = 65, speed = 15, color = P.primary) {{
  ctx.fillStyle = P.bg;
  ctx.fillRect(-300, -300, W + 600, H + 600);
  ctx.save();
  ctx.strokeStyle = color + '1C';
  ctx.lineWidth = 2;
  const h = size * Math.sqrt(3);
  const offY = (t * speed) % h;
  for (let y = -h + offY; y <= H + h; y += h) {{
    for (let x = -size; x <= W + size * 2; x += size * 3) {{
      for (let row = 0; row < 2; row++) {{
        const cx = x + (row === 1 ? size * 1.5 : 0);
        const cy = y + (row === 1 ? h / 2 : 0);
        ctx.beginPath();
        for (let a = 0; a < 6; a++) {{
          const angle = (Math.PI / 3) * a;
          const px = cx + size * 0.55 * Math.cos(angle);
          const py = cy + size * 0.55 * Math.sin(angle);
          if (a === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
        }}
        ctx.closePath();
        ctx.stroke();
      }}
    }}
  }}
  ctx.restore();
}}

/** 3D Perspective Warp Cosmic Starfield */
export function bgStarfield(t, count = 60, speed = 140, color = P.primary) {{
  ctx.fillStyle = P.bg;
  ctx.fillRect(-300, -300, W + 600, H + 600);
  ctx.save();
  const cx = W / 2, cy = 680;
  for (let i = 0; i < count; i++) {{
    const ang = rnd(i * 3) * TAU;
    const baseDist = rnd(i * 7) * 900;
    const dist = ((baseDist + t * speed) % 900);
    const px = cx + Math.cos(ang) * dist;
    const py = cy + Math.sin(ang) * dist;
    const r = 1 + (dist / 900) * 4;
    const alpha = clamp(dist / 900) * 0.65;
    circle(px, py, r, color + Math.floor(alpha * 255).toString(16).padStart(2, '0'));
  }}
  ctx.restore();
}}

/** Concentric Radar Telemetry Sweep */
export function bgRadar(t, speed = 1, color = P.secondary) {{
  ctx.fillStyle = P.bg;
  ctx.fillRect(-300, -300, W + 600, H + 600);
  ctx.save();
  const cx = W / 2, cy = 680;
  for (let r = 160; r <= 800; r += 160) {{
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, TAU);
    ctx.strokeStyle = color + '22';
    ctx.lineWidth = 2;
    ctx.stroke();
  }}
  line([[cx - 800, cy], [cx + 800, cy]], color + '1C', 2);
  line([[cx, cy - 800], [cx, cy + 800]], color + '1C', 2);
  const sweepAng = (t * speed * 1.5) % TAU;
  const grad = ctx.createRadialGradient(cx, cy, 20, cx, cy, 750);
  grad.addColorStop(0, P.accent + '2E');
  grad.addColorStop(1, 'transparent');
  ctx.beginPath();
  ctx.moveTo(cx, cy);
  ctx.arc(cx, cy, 750, sweepAng - 0.45, sweepAng);
  ctx.closePath();
  ctx.fillStyle = grad;
  ctx.fill();
  line([[cx, cy], [cx + Math.cos(sweepAng) * 750, cy + Math.sin(sweepAng) * 750]], P.accent + '80', 3);
  ctx.restore();
}}

/** Editorial / Engineering Blueprint Crosshair Background */
export function bgBlueprint(t, speed = 18, color = P.primary) {{
  ctx.fillStyle = P.bg;
  ctx.fillRect(-300, -300, W + 600, H + 600);
  ctx.save();
  const off = (t * speed) % 120;
  ctx.strokeStyle = color + '18';
  ctx.lineWidth = 2;
  for (let y = -120 + off; y <= H + 120; y += 120) {{
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
  }}
  for (let x = 60; x < W; x += 120) {{
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke();
  }}
  ctx.strokeStyle = P.accent + '28';
  for (let i = 0; i < 6; i++) {{
    const rx = 180 + (i % 3) * 360;
    const ry = 360 + Math.floor(i / 3) * 580 + Math.sin(t + i) * 14;
    line([[rx - 18, ry], [rx + 18, ry]], P.accent + '35', 3);
    line([[rx, ry - 18], [rx, ry + 18]], P.accent + '35', 3);
  }}
  ctx.restore();
}}

/** Dynamic Layered Wave Mesh Background */
export function bgWaveMesh(t, color = P.primary) {{
  ctx.fillStyle = P.bg;
  ctx.fillRect(-300, -300, W + 600, H + 600);
  ctx.save();
  for (let row = 0; row < 10; row++) {{
    const y0 = 180 + row * 165;
    ctx.beginPath();
    for (let x = -40; x <= W + 40; x += 40) {{
      const dy = Math.sin(x * 0.008 + t * 1.4 + row * 0.6) * 28;
      if (x === -40) ctx.moveTo(x, y0 + dy); else ctx.lineTo(x, y0 + dy);
    }}
    ctx.strokeStyle = (row % 2 === 0 ? color : P.secondary) + '26';
    ctx.lineWidth = 3;
    ctx.stroke();
  }}
  ctx.restore();
}}

/** Context-Aware Per-Shot Parallax Background Router */
export function bgThemeParallax(t, theme = 'COSMIC_SPACE', shotIndex = 0, bgMode = '') {{
  if (bgMode === 'STARFIELD') {{ bgStarfield(t, 55, 130); bgParticles(t, 20, P.accent); return; }}
  if (bgMode === 'HEX') {{ bgHex(t, 65, 16); bgParticles(t, 18, P.primary); return; }}
  if (bgMode === 'CONTOURS') {{ bgContours(t, 7, P.secondary); bgParticles(t, 18, P.accent); return; }}
  if (bgMode === 'RADAR') {{ bgRadar(t, 0.8, P.primary); bgConcentricWaves(t, 3, P.secondary); return; }}
  if (bgMode === 'BLUEPRINT') {{ bgBlueprint(t, 18, P.primary); return; }}
  if (bgMode === 'WAVEMESH') {{ bgWaveMesh(t, P.primary); bgParticles(t, 16, P.accent); return; }}

  if (theme === 'COSMIC_SPACE') {{
    bgStarfield(t, 55, 130);
    bgParticles(t, 25, P.accent);
  }} else if (theme === 'ATOMIC_PHYSICS') {{
    bgHex(t, 65, 16);
    bgParticles(t, 20, P.primary);
  }} else if (theme === 'SURVIVAL_TACTICAL') {{
    bgContours(t, 7, P.secondary);
    bgParticles(t, 20, P.accent);
  }} else if (theme === 'HISTORIC_DOCUMENTARY') {{
    bgRadar(t, 0.8, P.primary);
    bgConcentricWaves(t, 4, P.secondary);
  }} else {{
    bgGrid(t, 25);
    bgParticles(t, 30);
  }}
}}

// ═══════════════════════ PROCEDURAL TOPIC VECTORS (24+ SCENES) ═══════════════════════

/** Swirling 2D Black Hole with accretion disk */
export function drawBlackHole(x, y, r, t, pull = 0) {{
  ctx.save();
  ctx.translate(x, y);
  for (let i = 8; i >= 1; i--) {{
    const rad = r * (1.2 + i * 0.25);
    const ang = t * (0.8 + i * 0.2) * (i % 2 === 0 ? 1 : -1);
    ctx.save();
    ctx.rotate(ang);
    ctx.beginPath();
    ctx.ellipse(0, 0, rad, rad * 0.42, 0, 0, TAU);
    ctx.strokeStyle = (i % 2 === 0 ? P.primary : P.accent) + '40';
    ctx.lineWidth = 12 + i * 2;
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
  ctx.save();
  ctx.fillStyle = P.primary + '45';
  ctx.beginPath();
  ctx.moveTo(0, 0); ctx.lineTo(-110 * beam, -340); ctx.lineTo(110 * beam, -340); ctx.closePath();
  ctx.fill();
  ctx.beginPath();
  ctx.moveTo(0, 0); ctx.lineTo(-110 * beam, 340); ctx.lineTo(110 * beam, 340); ctx.closePath();
  ctx.fill();
  ctx.restore();
  circle(0, 0, r, P.primary);
  circle(0, 0, r * 0.65, '#FFFFFF');
  ctx.restore();
}}

/** Planetary Orbit & Exoplanet Revolution */
export function drawPlanetaryOrbit(x, y, r, t, count = 3) {{
  ctx.save();
  ctx.translate(x, y);
  circle(0, 0, 46, P.accent);
  for (let i = 1; i <= count; i++) {{
    const rad = r * (0.4 + i * 0.26);
    ctx.beginPath();
    ctx.arc(0, 0, rad, 0, TAU);
    ctx.strokeStyle = P.primary + '48';
    ctx.lineWidth = 3;
    ctx.stroke();
    const ang = t * (1.2 / i) + i * 2.1;
    const px = Math.cos(ang) * rad, py = Math.sin(ang) * rad;
    circle(px, py, 14 + i * 4, i % 2 === 0 ? P.primary : P.secondary);
  }}
  ctx.restore();
}}

/** Drifting Asteroid & Blast Debris Field */
export function drawAsteroidField(x, y, w, h, t, speed = 30) {{
  ctx.save();
  ctx.translate(x, y);
  for (let i = 0; i < 18; i++) {{
    const ox = ((rnd(i * 13) * w + t * speed * (0.8 + rnd(i))) % w) - w / 2;
    const oy = ((rnd(i * 29) * h + Math.sin(t + i) * 40) % h) - h / 2;
    const s = 16 + rnd(i * 7) * 26;
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
      const ox = (rnd(r * 11 + c) - 0.5) * dx * 1.2 * chaos;
      const oy = (rnd(r * 17 + c) - 0.5) * dy * 1.2 * chaos;
      const vib = Math.sin(t * 8 + r * 3 + c * 2) * (3 + chaos * 8);
      pts[r][c] = [c * dx + ox + vib, r * dy + oy + vib];
    }}
  }}
  ctx.lineWidth = 5;
  const bondColor = P.secondary + (chaos > 0.5 ? '50' : '99');
  for (let r = 0; r < rows; r++) {{
    for (let c = 0; c < cols; c++) {{
      if (c < cols - 1) line([pts[r][c], pts[r][c + 1]], bondColor, 4);
      if (r < rows - 1) line([pts[r][c], pts[r + 1][c]], bondColor, 4);
    }}
  }}
  for (let r = 0; r < rows; r++) {{
    for (let c = 0; c < cols; c++) {{
      const [px, py] = pts[r][c];
      circle(px, py, 18, P.primary);
      circle(px - 4, py - 4, 5, '#FFFFFF');
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
    const dist = (rnd(i * 31) * (r - 28));
    const px = Math.cos(ang) * dist, py = Math.sin(ang) * dist;
    circle(px, py, 11, i % 2 === 0 ? P.primary : P.accent);
  }}
  ctx.restore();
}}

/** Optical Prism Light Refraction */
export function drawPrismRefraction(x, y, r, t) {{
  ctx.save();
  ctx.translate(x, y);
  ctx.beginPath();
  ctx.moveTo(0, -r); ctx.lineTo(r, r * 0.8); ctx.lineTo(-r, r * 0.8); ctx.closePath();
  ctx.fillStyle = P.card + 'D0'; ctx.fill();
  ctx.strokeStyle = P.primary; ctx.lineWidth = 6; ctx.stroke();
  line([[-260, 40], [0, 0]], P.ink, 8);
  const colors = [P.danger, P.accent, P.primary, P.secondary];
  for (let i = 0; i < colors.length; i++) {{
    const yOff = -30 + i * 35 + Math.sin(t * 3 + i) * 4;
    line([[0, 0], [280, yOff]], colors[i], 8);
  }}
  ctx.restore();
}}

/** Quicksand Vortex */
export function drawQuicksandVortex(x, y, r, t, packing = 0) {{
  ctx.save();
  ctx.translate(x, y);
  for (let k = 6; k >= 1; k--) {{
    const rad = r * (0.3 + k * 0.14);
    const wobble = Math.sin(t * 3 + k) * 10;
    ctx.beginPath();
    ctx.ellipse(0, 0, rad + wobble, (rad + wobble) * 0.58, 0, 0, TAU);
    ctx.fillStyle = k % 2 === 0 ? P.card : P.secondary + '40';
    ctx.fill();
    ctx.strokeStyle = P.primary; ctx.lineWidth = 4; ctx.stroke();
  }}
  for (let i = 0; i < 36; i++) {{
    const dist = (i / 36) * r * (1 - packing * 0.35);
    const ang = i * 2.4 + t * (2 - packing * 1.4);
    circle(Math.cos(ang) * dist, Math.sin(ang) * dist * 0.58, 6, P.accent);
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
  const waterH = h * clamp(fill);
  ctx.save();
  ctx.beginPath();
  rr(-w/2, h/2 - waterH, w, waterH, 10);
  ctx.fillStyle = P.secondary + '60'; ctx.fill();
  ctx.restore();
  for (let i = -h/2 + 40; i <= h/2 - 40; i += 50) {{
    line([[-w/2 - 55, i], [-w/2 - 8, i]], P.danger, 6);
  }}
  ctx.restore();
}}

/** Acoustic Chamber & Resonator */
export function drawAcousticResonator(x, y, s, t, intensity = 1) {{
  ctx.save();
  ctx.translate(x, y); ctx.scale(s, s);
  rr(-200, -130, 400, 260, 36);
  ctx.fillStyle = P.card; ctx.fill();
  ctx.strokeStyle = P.primary; ctx.lineWidth = 8; ctx.stroke();
  for (let w = 0; w < 5; w++) {{
    const off = (t * 4 + w * 0.6) % 3;
    const alpha = clamp(1 - off / 3);
    ctx.beginPath();
    ctx.arc(130 + off * 70, 0, 36 + off * 54, -Math.PI * 0.4, Math.PI * 0.4);
    ctx.strokeStyle = P.danger + Math.floor(alpha * 255).toString(16).padStart(2, '0');
    ctx.lineWidth = 9 * intensity; ctx.stroke();
  }}
  ctx.restore();
}}

/** Thermal Vascular Gradient */
export function drawThermalGradient(x, y, w, h, coldRatio = 0.5, t = 0) {{
  ctx.save();
  ctx.translate(x, y);
  rr(-w/2, -h/2, w, h, 60);
  ctx.fillStyle = P.card; ctx.fill();
  ctx.strokeStyle = P.primary; ctx.lineWidth = 6; ctx.stroke();
  const coreR = (w / 3) * (1 - coldRatio * 0.38);
  circle(0, -18, coreR, P.danger + '80');
  circle(0, -18, coreR * 0.5, P.accent);
  for (let i = -w/2 + 30; i <= w/2 - 30; i += 40) {{
    line([[i, -h/2 + 20], [i, h/2 - 20]], P.primary + '45', 4);
  }}
  ctx.restore();
}}

/** Hydrodynamic Streamlines & Layered Waves */
export function drawHydroFlow(x, y, w, h, t, speed = 2) {{
  ctx.save();
  ctx.translate(x, y);
  rr(-w/2, -h/2, w, h, 28);
  ctx.fillStyle = P.card; ctx.fill();
  ctx.strokeStyle = P.primary; ctx.lineWidth = 6; ctx.stroke();
  ctx.save();
  ctx.beginPath();
  rr(-w/2 + 6, -h/2 + 6, w - 12, h - 12, 22);
  ctx.clip();
  // Animated layered fluid waves
  for (let layer = 0; layer < 3; layer++) {{
    const yBase = -20 + layer * 68;
    ctx.beginPath();
    ctx.moveTo(-w/2, h/2);
    for (let px = -w/2; px <= w/2; px += 24) {{
      const wy = yBase + Math.sin(px * 0.018 + t * (2.2 + layer * 0.6) + layer) * 22;
      ctx.lineTo(px, wy);
    }}
    ctx.lineTo(w/2, h/2); ctx.closePath();
    ctx.fillStyle = (layer === 0 ? P.primary : layer === 1 ? P.secondary : P.accent) + (layer === 2 ? '55' : '44');
    ctx.fill();
  }}
  ctx.restore();
  for (let row = -h/2 + 60; row <= h/2 - 60; row += 70) {{
    const offX = ((t * speed * 75) + Math.sin(row * 0.05 + t) * 25) % (w - 110);
    line([[-w/2 + 40 + offX, row], [-w/2 + 115 + offX, row]], P.danger, 6);
  }}
  line([[-40, 15], [w/2 - 55, 15]], P.accent, 10);
  circle(w/2 - 55, 15, 14, P.accent);
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

/** Ice Giant Diamond Rain Layered Atmosphere */
export function drawDiamondRain(x, y, w, h, t) {{
  ctx.save();
  ctx.translate(x, y);
  rr(-w/2, -h/2, w, h, 30);
  ctx.fillStyle = P.card; ctx.fill();
  ctx.strokeStyle = P.primary; ctx.lineWidth = 6; ctx.stroke();
  // Atmospheric pressure strata
  for (let i = 1; i <= 3; i++) {{
    const ly = -h/2 + (h / 4) * i;
    line([[-w/2 + 24, ly], [w/2 - 24, ly]], P.secondary + '45', 3);
  }}
  // Falling faceted diamonds
  for (let i = 0; i < 14; i++) {{
    const dx = -w/2 + 55 + ((i * 73) % (w - 110));
    const dy = -h/2 + 40 + ((t * (110 + (i % 4) * 35) + i * 55) % (h - 80));
    ctx.save();
    ctx.translate(dx, dy);
    ctx.beginPath();
    ctx.moveTo(0, -18); ctx.lineTo(14, 0); ctx.lineTo(0, 18); ctx.lineTo(-14, 0); ctx.closePath();
    ctx.fillStyle = i % 2 === 0 ? P.primary : P.accent;
    ctx.fill();
    ctx.strokeStyle = P.ink; ctx.lineWidth = 2; ctx.stroke();
    ctx.restore();
  }}
  ctx.restore();
}}

/** Grain Silo Funnel Entrapment Diagram */
export function drawGrainSilo(x, y, w, h, t, fill = 0.72) {{
  ctx.save();
  ctx.translate(x, y);
  rr(-w/2, -h/2, w, h, 24);
  ctx.fillStyle = P.card; ctx.fill();
  ctx.strokeStyle = P.primary; ctx.lineWidth = 6; ctx.stroke();
  const topY = -h/2 + h * (1 - clamp(fill, 0.2, 0.9));
  ctx.beginPath();
  ctx.moveTo(-w/2 + 12, topY);
  ctx.lineTo(-40, topY + 95);
  ctx.lineTo(40, topY + 95);
  ctx.lineTo(w/2 - 12, topY);
  ctx.lineTo(w/2 - 12, h/2 - 12);
  ctx.lineTo(-w/2 + 12, h/2 - 12);
  ctx.closePath();
  ctx.fillStyle = P.primary + 'AA'; ctx.fill();
  // Lateral locking force arrows
  for (const dir of [-1, 1]) {{
    const ax = dir * 130;
    line([[ax, topY + 70], [dir * 45, topY + 70]], P.danger, 8);
  }}
  // Central silhouette sunk in cone
  circle(0, topY + 35, 22, P.ink);
  rr(-20, topY + 58, 40, 52, 12);
  ctx.fillStyle = P.danger; ctx.fill();
  ctx.restore();
}}

/** Dense Crowd Compression Wave Simulation */
export function drawCrowdWave(x, y, w, h, t) {{
  ctx.save();
  ctx.translate(x, y);
  rr(-w/2, -h/2, w, h, 26);
  ctx.fillStyle = P.card; ctx.fill();
  ctx.strokeStyle = P.primary; ctx.lineWidth = 6; ctx.stroke();
  for (let row = 0; row < 5; row++) {{
    for (let col = 0; col < 8; col++) {{
      const wave = Math.sin(t * 4.5 - col * 0.65) * 14;
      const px = -w/2 + 65 + col * ((w - 130) / 7) + wave;
      const py = -h/2 + 65 + row * ((h - 130) / 4);
      const compressed = wave > 6;
      circle(px, py, 16, compressed ? P.danger : P.primary);
    }}
  }}
  // Diagonal escape vector arrow
  line([[-w/2 + 70, h/2 - 50], [w/2 - 70, -h/2 + 60]], P.accent, 8);
  circle(w/2 - 70, -h/2 + 60, 12, P.accent);
  ctx.restore();
}}

/** Avalanche Strata & Emergency Breathing Pocket */
export function drawAvalancheLayers(x, y, w, h, t) {{
  ctx.save();
  ctx.translate(x, y);
  rr(-w/2, -h/2, w, h, 26);
  ctx.fillStyle = P.card; ctx.fill();
  ctx.strokeStyle = P.primary; ctx.lineWidth = 6; ctx.stroke();
  // Packed snow slab strata
  for (let k = 0; k < 4; k++) {{
    const sy = -h/2 + 80 + k * 80;
    ctx.beginPath();
    ctx.moveTo(-w/2 + 12, sy);
    ctx.lineTo(w/2 - 12, sy + 35);
    ctx.strokeStyle = P.secondary + '80'; ctx.lineWidth = 5; ctx.stroke();
  }}
  // Protected air pocket dome
  const pulse = 1 + Math.sin(t * 4) * 0.05;
  circle(0, 40, 68 * pulse, P.primary + '35');
  ctx.beginPath(); ctx.arc(0, 40, 68 * pulse, 0, TAU);
  ctx.strokeStyle = P.accent; ctx.lineWidth = 6; ctx.stroke();
  circle(0, 40, 22, P.ink);
  ctx.restore();
}}

/** Volcanic Eruption & Stratospheric Veil */
export function drawVolcanoPlume(x, y, w, h, t) {{
  ctx.save();
  ctx.translate(x, y);
  rr(-w/2, -h/2, w, h, 26);
  ctx.fillStyle = P.card; ctx.fill();
  ctx.strokeStyle = P.primary; ctx.lineWidth = 6; ctx.stroke();
  // Stratospheric sulfuric cloud veil blocking sun rays
  for (let i = 0; i < 6; i++) {{
    const cx = -180 + i * 72 + Math.sin(t * 1.5 + i) * 14;
    circle(cx, -h/2 + 95, 42 + (i % 2) * 12, P.secondary + 'AA');
  }}
  // Mountain cone
  ctx.beginPath();
  ctx.moveTo(-170, h/2 - 20); ctx.lineTo(-32, 30); ctx.lineTo(32, 30); ctx.lineTo(170, h/2 - 20); ctx.closePath();
  ctx.fillStyle = P.primary + '55'; ctx.fill();
  ctx.strokeStyle = P.primary; ctx.lineWidth = 5; ctx.stroke();
  // Eruption plume column
  line([[0, 30], [0, -h/2 + 95]], P.danger, 18);
  ctx.restore();
}}

/** Corium / Radioactive Core & Geiger Waves */
export function drawRadiationCore(x, y, r, t) {{
  ctx.save();
  ctx.translate(x, y);
  for (let i = 3; i >= 1; i--) {{
    const rad = r * (0.6 + i * 0.25) + Math.sin(t * 5 - i) * 8;
    ctx.beginPath(); ctx.arc(0, 0, rad, 0, TAU);
    ctx.strokeStyle = P.accent + '55'; ctx.lineWidth = 5; ctx.stroke();
  }}
  circle(0, 0, r * 0.55, P.card);
  ctx.strokeStyle = P.accent; ctx.lineWidth = 6; ctx.stroke();
  for (let k = 0; k < 3; k++) {{
    const a0 = k * (TAU / 3) + t * 0.6;
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.arc(0, 0, r * 0.44, a0, a0 + 0.95);
    ctx.closePath();
    ctx.fillStyle = P.accent; ctx.fill();
  }}
  circle(0, 0, 18, P.danger);
  ctx.restore();
}}

/** Step Potential Ground Voltage Gradient */
export function drawStepVoltage(x, y, w, h, t) {{
  ctx.save();
  ctx.translate(x, y);
  rr(-w/2, -h/2, w, h, 26);
  ctx.fillStyle = P.card; ctx.fill();
  ctx.strokeStyle = P.primary; ctx.lineWidth = 6; ctx.stroke();
  for (let i = 4; i >= 1; i--) {{
    const rx = i * 62;
    const ry = i * 38;
    ctx.beginPath();
    ctx.ellipse(0, 20, rx, ry, 0, 0, TAU);
    ctx.strokeStyle = (i <= 2 ? P.danger : P.accent) + (i === 1 ? 'FF' : '99');
    ctx.lineWidth = 6; ctx.stroke();
  }}
  circle(0, 20, 14, P.danger);
  line([[-24, -130], [0, 20]], P.accent, 6);
  ctx.restore();
}}

/** Heavy Gas Valley Blanket (Lake Nyos / Carbon Monoxide) */
export function drawGasValley(x, y, w, h, t) {{
  ctx.save();
  ctx.translate(x, y);
  rr(-w/2, -h/2, w, h, 26);
  ctx.fillStyle = P.card; ctx.fill();
  ctx.strokeStyle = P.primary; ctx.lineWidth = 6; ctx.stroke();
  // Valley slopes
  ctx.beginPath();
  ctx.moveTo(-w/2 + 12, -40); ctx.lineTo(-90, 90); ctx.lineTo(90, 90); ctx.lineTo(w/2 - 12, -20);
  ctx.lineTo(w/2 - 12, h/2 - 12); ctx.lineTo(-w/2 + 12, h/2 - 12); ctx.closePath();
  ctx.fillStyle = P.secondary + '40'; ctx.fill();
  // Drifting dense gas layer
  for (let i = 0; i < 7; i++) {{
    const gx = -180 + i * 60 + Math.sin(t * 2 + i) * 16;
    circle(gx, 45 + (i % 2) * 18, 46, P.danger + '70');
  }}
  ctx.restore();
}}

/** Slot Canyon Walls & Flash Flood Surge */
export function drawCanyonSurge(x, y, w, h, t) {{
  ctx.save();
  ctx.translate(x, y);
  rr(-w/2, -h/2, w, h, 26);
  ctx.fillStyle = P.card; ctx.fill();
  ctx.strokeStyle = P.primary; ctx.lineWidth = 6; ctx.stroke();
  // Narrow steep canyon walls
  ctx.fillStyle = P.secondary + '55';
  ctx.fillRect(-w/2 + 14, -h/2 + 20, 120, h - 40);
  ctx.fillRect(w/2 - 134, -h/2 + 20, 120, h - 40);
  // Surging water wall inside slot
  const surgeH = 110 + Math.sin(t * 4) * 24;
  ctx.fillStyle = P.primary + 'AA';
  ctx.fillRect(-w/2 + 134, h/2 - 20 - surgeH, w - 268, surgeH);
  // Upward escape arrow
  line([[0, 20], [0, -120]], P.accent, 8);
  circle(0, -120, 12, P.accent);
  ctx.restore();
}}

/** Deep Sea Submersible Pressure Shell & Implosion Arrows */
export function drawSubmersibleHull(x, y, w, h, t) {{
  ctx.save();
  ctx.translate(x, y);
  const crush = 1 - Math.abs(Math.sin(t * 3.5)) * 0.08;
  rr(-160 * crush, -95 * crush, 320 * crush, 190 * crush, 95 * crush);
  ctx.fillStyle = P.card; ctx.fill();
  ctx.strokeStyle = P.primary; ctx.lineWidth = 8; ctx.stroke();
  circle(-60 * crush, 0, 32, P.accent + '70');
  for (const [sx, sy, tx, ty] of [[-240, 0, -180, 0], [240, 0, 180, 0], [0, -165, 0, -110], [0, 165, 0, 110]]) {{
    line([[sx, sy], [tx, ty]], P.danger, 8);
  }}
  ctx.restore();
}}

/** Waving National Flag / Pennant Swatch */
export function drawFlagEmblem(x, y, w, h, t) {{
  ctx.save();
  ctx.translate(x, y);
  line([[-w/2 + 70, -h/2 + 20], [-w/2 + 70, h/2 - 20]], P.ink, 10);
  ctx.beginPath();
  ctx.moveTo(-w/2 + 80, -h/2 + 35);
  for (let px = 0; px <= 340; px += 34) {{
    ctx.lineTo(-w/2 + 80 + px, -h/2 + 35 + Math.sin(t * 4 + px * 0.03) * 14);
  }}
  for (let px = 340; px >= 0; px -= 34) {{
    ctx.lineTo(-w/2 + 80 + px, h/2 - 75 + Math.sin(t * 4 + px * 0.03) * 14);
  }}
  ctx.closePath();
  ctx.fillStyle = P.primary; ctx.fill();
  ctx.strokeStyle = P.ink; ctx.lineWidth = 5; ctx.stroke();
  circle(-w/2 + 230, -15, 36, P.accent);
  ctx.restore();
}}

/** Archival Route Map & Historical Marker */
export function drawArchiveMap(x, y, w, h, t) {{
  ctx.save();
  ctx.translate(x, y);
  rr(-w/2, -h/2, w, h, 24);
  ctx.fillStyle = P.card; ctx.fill();
  ctx.strokeStyle = P.primary; ctx.lineWidth = 6; ctx.stroke();
  const pts = [[-190, 80], [-70, -50], [60, 20], [190, -70]];
  ctx.setLineDash([14, 10]);
  line(pts, P.danger, 6);
  ctx.setLineDash([]);
  for (let i = 0; i < pts.length; i++) {{
    const pulse = i === Math.floor(t % pts.length) ? 1.35 : 1.0;
    circle(pts[i][0], pts[i][1], 16 * pulse, i === pts.length - 1 ? P.danger : P.accent);
  }}
  ctx.restore();
}}

// ═══════════════════════ HUD GAUGES & SAFE-ZONE CALLOUTS ═══════════════════════

export function drawProgressStrip(t, dur) {{
  const ratio = clamp(t / Math.max(0.1, dur));
  ctx.save();
  ctx.fillStyle = P.card;
  ctx.fillRect(90, 96, 900, 10);
  ctx.fillStyle = P.accent;
  ctx.fillRect(90, 96, 900 * ratio, 10);
  ctx.restore();
}}

export function drawPointerTag(text, x, y, tx, ty, sc = 1) {{
  if (sc <= 0) return;
  ctx.save();
  ctx.globalAlpha = clamp(sc);
  line([[x, y], [tx, ty]], P.accent, 6);
  circle(tx, ty, 10, P.accent);
  ctx.restore();
  drawTopicPill(text, x, y, sc);
}}

export function drawImpactStamp(kind, x, y, sc = 1) {{
  if (sc <= 0) return;
  ctx.save();
  ctx.translate(x, y); ctx.scale(sc, sc);
  ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  if (kind === 'x') {{
    ctx.strokeStyle = P.ink; ctx.lineWidth = 34;
    ctx.beginPath(); ctx.moveTo(-90, -90); ctx.lineTo(90, 90); ctx.moveTo(90, -90); ctx.lineTo(-90, 90); ctx.stroke();
    ctx.strokeStyle = P.danger; ctx.lineWidth = 22;
    ctx.beginPath(); ctx.moveTo(-90, -90); ctx.lineTo(90, 90); ctx.moveTo(90, -90); ctx.lineTo(-90, 90); ctx.stroke();
  }} else {{
    ctx.strokeStyle = P.ink; ctx.lineWidth = 34;
    ctx.beginPath(); ctx.moveTo(-85, 5); ctx.lineTo(-20, 70); ctx.lineTo(95, -75); ctx.stroke();
    ctx.strokeStyle = P.accent; ctx.lineWidth = 22;
    ctx.beginPath(); ctx.moveTo(-85, 5); ctx.lineTo(-20, 70); ctx.lineTo(95, -75); ctx.stroke();
  }}
  ctx.restore();
}}

export function drawRadialGauge(x, y, r, valRatio, label, valText, sc = 1) {{
  if (sc <= 0) return;
  ctx.save();
  ctx.translate(x, y); ctx.scale(sc, sc);
  ctx.beginPath();
  ctx.arc(0, 0, r, Math.PI * 0.75, Math.PI * 2.25);
  ctx.strokeStyle = P.card; ctx.lineWidth = 22; ctx.lineCap = 'round'; ctx.stroke();
  const sweep = Math.PI * 1.5 * clamp(valRatio);
  ctx.beginPath();
  ctx.arc(0, 0, r, Math.PI * 0.75, Math.PI * 0.75 + sweep);
  ctx.strokeStyle = P.primary; ctx.lineWidth = 22; ctx.lineCap = 'round';
  ctx.shadowColor = P.primary; ctx.shadowBlur = 15; ctx.stroke();
  ctx.shadowBlur = 0;

  const vt = String(valText).toUpperCase();
  let vfs = Math.round(r * 0.34);
  ctx.font = `900 ${{vfs}}px Inter`;
  while (vfs > 18 && ctx.measureText(vt).width > r * 1.38) {{
    vfs -= 2;
    ctx.font = `900 ${{vfs}}px Inter`;
  }}
  ctx.fillStyle = P.ink; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.fillText(vt, 0, -4);

  const lt = String(label).toUpperCase();
  let lfs = 24;
  ctx.font = `800 ${{lfs}}px Inter`;
  while (lfs > 16 && ctx.measureText(lt).width > 760) {{
    lfs -= 2;
    ctx.font = `800 ${{lfs}}px Inter`;
  }}
  ctx.fillStyle = P.subtext;
  ctx.fillText(lt, 0, r + 38);
  ctx.restore();
}}

export function drawComparisonBar(x, y, w, h, ratioA, labelA, labelB, sc = 1) {{
  if (sc <= 0) return;
  ctx.save();
  ctx.translate(x - w / 2, y); ctx.scale(sc, sc);
  rr(0, 0, w, h, h / 2);
  ctx.fillStyle = P.card; ctx.fill();
  ctx.strokeStyle = P.primary + '55'; ctx.lineWidth = 3; ctx.stroke();
  const wA = w * clamp(ratioA);
  rr(0, 0, wA, h, h / 2);
  ctx.fillStyle = P.primary; ctx.fill();
  ctx.font = '900 24px Inter'; ctx.fillStyle = P.ink; ctx.textAlign = 'left'; ctx.textBaseline = 'bottom';
  ctx.fillText(String(labelA).toUpperCase(), 12, -14);
  ctx.textAlign = 'right'; ctx.fillStyle = P.accent;
  ctx.fillText(String(labelB).toUpperCase(), w - 12, -14);
  ctx.restore();
}}

export function drawStepCard(stepNum, title, x, y, sc = 1) {{
  if (sc <= 0) return;
  ctx.save();
  ctx.translate(x, y); ctx.scale(sc, sc);
  const w = 840, h = 116;
  rr(-w / 2, -h / 2, w, h, 24);
  ctx.fillStyle = P.primary; ctx.shadowColor = 'rgba(0,0,0,0.35)';
  ctx.shadowBlur = 20; ctx.shadowOffsetY = 8; ctx.fill();
  circle(-w / 2 + 64, 0, 38, P.card);
  ctx.font = '900 34px Inter'; ctx.fillStyle = P.accent; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.fillText(String(stepNum), -w / 2 + 64, 2);
  const txt = title.toUpperCase();
  let fs = 32;
  ctx.font = `900 ${{fs}}px Inter`;
  while (fs > 20 && ctx.measureText(txt).width > w - 165) {{
    fs -= 2;
    ctx.font = `900 ${{fs}}px Inter`;
  }}
  ctx.fillStyle = P.on_primary || '#0F172A'; ctx.textAlign = 'left';
  ctx.fillText(txt, -w / 2 + 124, 2);
  ctx.restore();
}}

export function drawHazardBanner(text, x, y, sc = 1) {{
  if (sc <= 0) return;
  ctx.save();
  ctx.translate(x, y); ctx.rotate(-0.03); ctx.scale(sc, sc);
  const w = 840, h = 118;
  rr(-w / 2, -h / 2, w, h, 22);
  ctx.fillStyle = P.danger; ctx.shadowColor = 'rgba(239,68,68,0.45)'; ctx.shadowBlur = 24; ctx.fill();
  const txt = '! ' + text.toUpperCase();
  let fs = 36;
  ctx.font = `900 ${{fs}}px Inter`;
  while (fs > 22 && ctx.measureText(txt).width > w - 60) {{
    fs -= 2;
    ctx.font = `900 ${{fs}}px Inter`;
  }}
  ctx.fillStyle = '#FFFFFF'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.fillText(txt, 0, 2);
  ctx.restore();
}}

export function drawTopicPill(text, x, y, sc = 1) {{
  if (sc <= 0) return;
  ctx.save();
  ctx.translate(x, y); ctx.scale(sc, sc);
  ctx.font = '900 28px Inter';
  const tw = Math.min(920, ctx.measureText(text.toUpperCase()).width + 72);
  rr(-tw / 2, -30, tw, 60, 30);
  ctx.fillStyle = P.card; ctx.strokeStyle = P.primary; ctx.lineWidth = 3; ctx.fill(); ctx.stroke();
  ctx.fillStyle = P.primary; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.fillText(text.toUpperCase(), 0, 2);
  ctx.restore();
}}

export function drawBigStat(valText, label, x, y, sc = 1, accentColor = P.accent) {{
  if (sc <= 0) return;
  ctx.save();
  ctx.translate(x, y); ctx.scale(sc, sc);
  const w = 840, h = 216;
  rr(-w / 2, -h / 2, w, h, 26);
  ctx.fillStyle = P.card; ctx.shadowColor = accentColor + '35'; ctx.shadowBlur = 24; ctx.fill();
  ctx.strokeStyle = accentColor; ctx.lineWidth = 4; ctx.stroke();
  const vt = String(valText).toUpperCase();
  let vfs = 70;
  ctx.font = `900 ${{vfs}}px Inter`;
  while (vfs > 34 && ctx.measureText(vt).width > w - 70) {{
    vfs -= 4;
    ctx.font = `900 ${{vfs}}px Inter`;
  }}
  ctx.fillStyle = P.ink; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.fillText(vt, 0, -24);
  const lt = String(label).toUpperCase();
  let lfs = 24;
  ctx.font = `900 ${{lfs}}px Inter`;
  while (lfs > 16 && ctx.measureText(lt).width > w - 60) {{
    lfs -= 2;
    ctx.font = `900 ${{lfs}}px Inter`;
  }}
  ctx.fillStyle = accentColor;
  ctx.fillText(lt, 0, 48);
  ctx.restore();
}}

export function drawSplitComparison(labelA, titleA, labelB, titleB, x, y, sc = 1) {{
  if (sc <= 0) return;
  ctx.save();
  ctx.translate(x, y); ctx.scale(sc, sc);
  const boxW = 400, boxH = 360;
  const fitText = (txt, maxW, startSize) => {{
    let fs = startSize;
    ctx.font = `900 ${{fs}}px Inter`;
    while (fs > 18 && ctx.measureText(txt).width > maxW) {{ fs -= 2; ctx.font = `900 ${{fs}}px Inter`; }}
  }};
  rr(-boxW - 18, -boxH / 2, boxW, boxH, 26);
  ctx.fillStyle = P.card; ctx.fill();
  ctx.strokeStyle = P.danger; ctx.lineWidth = 5; ctx.stroke();
  fitText(labelA.toUpperCase(), boxW - 40, 24);
  ctx.fillStyle = P.danger; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.fillText(labelA.toUpperCase(), -boxW / 2 - 18, -boxH / 2 + 60);
  fitText(titleA.toUpperCase(), boxW - 40, 34);
  ctx.fillStyle = P.ink;
  ctx.fillText(titleA.toUpperCase(), -boxW / 2 - 18, 20);

  rr(18, -boxH / 2, boxW, boxH, 26);
  ctx.fillStyle = P.card; ctx.fill();
  ctx.strokeStyle = P.accent; ctx.lineWidth = 5; ctx.stroke();
  fitText(labelB.toUpperCase(), boxW - 40, 24);
  ctx.fillStyle = P.accent; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.fillText(labelB.toUpperCase(), boxW / 2 + 18, -boxH / 2 + 60);
  fitText(titleB.toUpperCase(), boxW - 40, 34);
  ctx.fillStyle = P.ink;
  ctx.fillText(titleB.toUpperCase(), boxW / 2 + 18, 20);

  circle(0, 0, 38, P.card);
  ctx.strokeStyle = P.primary; ctx.lineWidth = 4; ctx.stroke();
  ctx.font = '900 24px Inter'; ctx.fillStyle = P.primary; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.fillText('VS', 0, 2);
  ctx.restore();
}}

export function drawWaveform(x, y, w, h, t, freq = 3, label = '', sc = 1) {{
  if (sc <= 0) return;
  ctx.save();
  ctx.translate(x, y); ctx.scale(sc, sc);
  rr(-w / 2, -h / 2, w, h, 24);
  ctx.fillStyle = P.card; ctx.fill();
  ctx.strokeStyle = P.primary; ctx.lineWidth = 4; ctx.stroke();
  ctx.strokeStyle = P.primary + '1C'; ctx.lineWidth = 1;
  for (let gy = -h / 2 + 30; gy <= h / 2 - 30; gy += 40) {{
    ctx.beginPath(); ctx.moveTo(-w / 2 + 20, gy); ctx.lineTo(w / 2 - 20, gy); ctx.stroke();
  }}
  ctx.beginPath();
  for (let wx = -w / 2 + 30; wx <= w / 2 - 30; wx += 6) {{
    const normX = (wx / (w / 2));
    const amp = (h / 3) * Math.sin(normX * freq + t * 4);
    if (wx === -w / 2 + 30) ctx.moveTo(wx, amp); else ctx.lineTo(wx, amp);
  }}
  ctx.strokeStyle = P.accent; ctx.lineWidth = 5; ctx.shadowColor = P.accent; ctx.shadowBlur = 12; ctx.stroke();
  if (label) {{
    ctx.font = '900 22px Inter'; ctx.fillStyle = P.primary; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(label.toUpperCase(), 0, -h / 2 + 28);
  }}
  ctx.restore();
}}

export function drawPipelineNodes(x, y, w, activeStep = 1, labels = [], sc = 1) {{
  if (sc <= 0 || !labels || !labels.length) return;
  ctx.save();
  ctx.translate(x, y); ctx.scale(sc, sc);
  const count = labels.length;
  const gap = count > 1 ? w / (count - 1) : 0;
  line([[-w / 2, 0], [w / 2, 0]], P.primary + '45', 8);
  const progLine = -w / 2 + clamp(activeStep - 1, 0, count - 1) * gap;
  if (progLine > -w / 2) {{
    line([[-w / 2, 0], [progLine, 0]], P.accent, 8);
  }}
  for (let i = 0; i < count; i++) {{
    const nx = -w / 2 + i * gap;
    const isActive = (i + 1) <= activeStep;
    circle(nx, 0, 34, isActive ? P.accent : P.card);
    ctx.strokeStyle = isActive ? P.ink : P.primary; ctx.lineWidth = 4; ctx.stroke();
    ctx.font = '900 26px Inter'; ctx.fillStyle = isActive ? (P.on_primary || '#0F172A') : P.primary;
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(String(i + 1), nx, 2);
    ctx.font = '900 20px Inter'; ctx.fillStyle = isActive ? P.ink : P.subtext;
    ctx.fillText(String(labels[i]).toUpperCase(), nx, 58);
  }}
  ctx.restore();
}}
"""


# ═════════════════════════════════════════════════════════════════════════════
# 5. CONTENT-AWARE SHOT GENERATOR (src/shots.js) — Caption-Safe & Word-Synced
# ═════════════════════════════════════════════════════════════════════════════

def generate_shots_js(
    title: str,
    topic: str,
    lines: List[Dict],
    theme: str,
    palette: Dict[str, Any],
    asset_seed: str = "",
    visual_plan: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[str, List[str], str]:
    """Generates dynamic, bespoke shots.js with safe-zone placement (y=190..1180) and Wd() sync.

    Returns:
        (shots_js_code, scene_sequence_archetypes, focal_vector_name)
    """
    plan = compose_video_visual_plan(
        title=title,
        topic=topic,
        lines=lines,
        theme=theme,
        asset_seed=asset_seed,
        visual_plan=visual_plan,
    )
    return generate_shots_js_from_plan(plan)


def generate_shots_js_from_plan(plan: Dict[str, Any]) -> Tuple[str, List[str], str]:
    """Serializes a verified visual plan into valid, word-synced JavaScript shots.js."""
    theme = plan["theme"]
    vector_name = plan["vector_name"]
    shots_spec = plan["shots"]
    scene_sequence = plan["scene_sequence"]

    shot_blocks: List[str] = []
    for sp in shots_spec:
        i = sp["index"]
        shot_id = f"S{i+1:02d}"
        kind = sp["kind"]
        bg_mode = json.dumps(sp["bg_mode"])
        sub_bg_mode = json.dumps(sp.get("sub_bg_mode", sp["bg_mode"]))
        has_subcut = bool(sp.get("has_subcut", False))
        theme_js = json.dumps(theme)
        pill_js = json.dumps(sp["pill"])
        focus_js = json.dumps(sp["focus_word"])
        cd = sp["card_data"]
        sfx = json.dumps(sp["sfx"])
        cx = sp["cam_x"]
        cy = sp["cam_y"]
        zoom = sp["cam_zoom"]
        sub_cx = 540 + (26 if cx == 540 else -cx + 540)
        sub_zoom = round(zoom + 0.03, 2)

        def _wrap_middle_or_subcut(note: str, stage_expr_a: str, stage_expr_b: str, sfx_gain: float = 0.6) -> str:
            if not has_subcut:
                return f"""
  {{ const st = cut({i});
    const fw = {focus_js};
    const hit = fw ? Math.max(0.15, Wd(fw, {i}) - st) : 0.3;
    add({{ id: '{shot_id}', at: st, cam: [{cx}, {cy}], zoom: {zoom}, note: {json.dumps(note)}, draw(lt, d, t) {{
      K.bgThemeParallax(t, {theme_js}, {i}, {bg_mode});
      K.drawProgressStrip(t, T.dur);
      K.drawTopicPill({pill_js}, 540, 195, eob(seg(lt, 0.05, 0.35)));
      {stage_expr_b}
    }} }});
    cue(st, 'whoosh', {{ gain: 0.45 }}); cue(st + hit, {sfx}, {{ gain: {sfx_gain} }}); }}"""
            beat_b_expr = re.sub(
                r'lt\s*>\s*hit\s*\?\s*eob\(seg\(lt,\s*hit,\s*hit\s*\+\s*0\.\d+\)\)\s*:\s*eob\(seg\(lt,\s*0\.\d+,\s*0\.\d+\)\)',
                'eob(seg(lt, 0.04, 0.30))',
                stage_expr_b,
            )
            beat_b_expr = re.sub(
                r'\(\s*lt\s*>\s*hit\s*\?\s*eob\(seg\(lt,\s*hit,\s*hit\s*\+\s*0\.\d+\)\)\s*:\s*eob\(seg\(lt,\s*0\.\d+,\s*0\.\d+\)\)\s*\)',
                'eob(seg(lt, 0.04, 0.28))',
                beat_b_expr,
            )
            return f"""
  {{ const st = cut({i});
    const fw = {focus_js};
    const rawSplit = fw ? Wd(fw, {i}) - 0.08 : st + 2.0;
    const nextSt = ({i} + 1 < T.lines.length) ? cut({i} + 1) : T.dur;
    const splitAt = (rawSplit > st + 1.4 && rawSplit < nextSt - 1.0) ? rawSplit : (st + (nextSt - st) * 0.52);
    add({{ id: '{shot_id}a', at: st, cam: [{cx}, {cy}], zoom: {zoom}, note: {json.dumps(note + ' (setup)')}, draw(lt, d, t) {{
      K.bgThemeParallax(t, {theme_js}, {i}, {bg_mode});
      K.drawProgressStrip(t, T.dur);
      K.drawTopicPill({pill_js}, 540, 195, eob(seg(lt, 0.04, 0.32)));
      {stage_expr_a}
    }} }});
    add({{ id: '{shot_id}b', at: splitAt, cam: [{sub_cx}, 710], zoom: {sub_zoom}, note: {json.dumps(note + ' (beat B sub-cut)')}, draw(lt, d, t) {{
      K.bgThemeParallax(t, {theme_js}, {i + 7}, {sub_bg_mode});
      K.drawProgressStrip(t, T.dur);
      K.drawTopicPill({pill_js}, 540, 195, eob(seg(lt, 0.02, 0.24)));
      {beat_b_expr}
    }} }});
    cue(st, 'whoosh', {{ gain: 0.42 }}); cue(splitAt, 'pop', {{ gain: 0.5 }}); cue(splitAt + 0.14, {sfx}, {{ gain: {sfx_gain} }}); }}"""

        # Safe vertical budget:
        #   Progress bar: y = 96
        #   Topic Pill:   y = 195
        #   Hero scene:   y = 420..880 (center ~620-660)
        #   Bottom card:  y = 1000..1160 (strictly ABOVE y=1230 caption zone!)
        if i == 0:
            hero_call = _vector_draw_call(vector_name, is_hook=True)
            hook_callout = json.dumps(cd["hook_callout"])
            hook_sub_js = json.dumps(cd.get("hook_sub", sp["pill"]))
            block = f"""
  {{ const st = cut({i});
    const fw = {focus_js};
    const hit = fw ? Math.max(0.15, Wd(fw, {i}) - st) : 0.35;
    add({{ id: '{shot_id}', at: st, cam: [{cx}, {cy}], zoom: {zoom}, note: 'Hook: bright frame-0 hero illustration + hook spotlight', draw(lt, d, t) {{
      K.bgThemeParallax(t, {theme_js}, {i}, {bg_mode});
      K.drawProgressStrip(t, T.dur);
      K.drawTopicPill({pill_js}, 540, 195, 0.88 + 0.12 * eob(seg(lt, 0, 0.24)));
      {hero_call}
      K.drawBigStat({hook_callout}, {hook_sub_js}, 540, 1050, 0.88 + 0.12 * eob(seg(lt, 0, 0.28)));
    }} }});
    cue(st + hit, {sfx}, {{ gain: 0.6 }}); }}"""

        elif kind == "LOOP_OUTRO":
            hero_call = _vector_draw_call(vector_name, is_hook=False)
            takeaway_js = json.dumps(cd["takeaway"])
            loop_js = json.dumps(cd["loop_label"])
            block = f"""
  {{ const st = cut({i});
    const fw = {focus_js};
    const hit = fw ? Math.max(0.15, Wd(fw, {i}) - st) : 0.3;
    add({{ id: '{shot_id}', at: st, cam: [{cx}, {cy}], zoom: {zoom}, note: 'Outro: seamless topic loopback takeaway', draw(lt, d, t) {{
      K.bgThemeParallax(t, {theme_js}, {i}, {bg_mode});
      K.drawProgressStrip(t, T.dur);
      K.drawTopicPill({pill_js}, 540, 195, eob(seg(lt, 0.04, 0.28)));
      {hero_call}
      K.drawBigStat({takeaway_js}, {loop_js}, 540, 1040, eob(seg(lt, 0.12, 0.38)));
    }} }});
    cue(st, 'whoosh', {{ gain: 0.45 }}); cue(st + hit, {sfx}, {{ gain: 0.62 }}); }}"""

        elif kind.startswith("MECH_"):
            mech_call_a = _vector_draw_call(vector_name, is_hook=True)
            mech_call = _vector_draw_call(vector_name, is_hook=False)
            ptr_js = json.dumps(cd["pointer_label"])
            block = _wrap_middle_or_subcut(
                "Mechanism diagram + word-synced pointer tag",
                mech_call_a,
                f"{mech_call}\n      K.drawPointerTag({ptr_js}, 540, 1060, 540, 820, lt > hit ? eob(seg(lt, hit, hit + 0.25)) : eob(seg(lt, 0.15, 0.42)));",
                sfx_gain=0.55,
            )

        elif kind == "COMPARE_SPLIT":
            la = json.dumps(cd["label_a"])
            ta = json.dumps(cd["title_a"])
            lb = json.dumps(cd["label_b"])
            tb = json.dumps(cd["title_b"])
            hero_a = _vector_draw_call(vector_name, is_hook=True)
            block = _wrap_middle_or_subcut(
                "Full-stage contrast split comparison",
                f"{hero_a}\n      K.drawBigStat({ta}, {la}, 540, 1050, eob(seg(lt, 0.08, 0.34)));",
                f"K.drawSplitComparison({la}, {ta}, {lb}, {tb}, 540, 680, lt > hit ? eob(seg(lt, hit, hit + 0.28)) : eob(seg(lt, 0.10, 0.38)));\n      K.drawImpactStamp('x', 320, 420, eob(seg(lt, 0.14, 0.38)) * 0.55);\n      K.drawImpactStamp('check', 760, 420, eob(seg(lt, 0.18, 0.42)) * 0.55);",
                sfx_gain=0.6,
            )

        elif kind == "BIG_STAT_METRIC":
            val_js = json.dumps(cd["value"])
            lbl_js = json.dumps(cd["label"])
            hero_a = _vector_draw_call(vector_name, is_hook=True)
            block = _wrap_middle_or_subcut(
                "Hero quantitative stat stage",
                hero_a,
                f"K.drawBigStat({val_js}, {lbl_js}, 540, 680, lt > hit ? eob(seg(lt, hit, hit + 0.28)) : eob(seg(lt, 0.10, 0.38)));",
                sfx_gain=0.6,
            )

        elif kind == "WAVE_OSCILLATION":
            wave_js = json.dumps(cd["wave_label"])
            hero_a = _vector_draw_call(vector_name, is_hook=False)
            block = _wrap_middle_or_subcut(
                "Full-stage animated frequency wave",
                hero_a,
                f"K.drawWaveform(540, 680, 860, 420, lt, 3.6, {wave_js}, eob(seg(lt, 0.10, 0.38)));",
                sfx_gain=0.6,
            )

        elif kind == "PIPELINE_FLOW":
            stages_js = json.dumps(cd["stages"])
            active_step = cd["active"]
            mech_a = _vector_draw_call(vector_name, is_hook=True)
            mech_call = _vector_draw_call(vector_name, is_hook=False)
            block = _wrap_middle_or_subcut(
                "Topic causal progression stage",
                mech_a,
                f"ctx.save(); ctx.translate(0, -80); ctx.scale(0.88, 0.88); ctx.translate(72, 0);\n      {mech_call}\n      ctx.restore();\n      K.drawPipelineNodes(540, 990, 740, {active_step}, {stages_js}, lt > hit ? eob(seg(lt, hit, hit + 0.25)) : eob(seg(lt, 0.12, 0.4)));",
                sfx_gain=0.55,
            )

        elif kind == "METRIC_TELEMETRY":
            val_js = json.dumps(cd["value"])
            lbl_js = json.dumps(cd["label"])
            ratio = cd["ratio"]
            hero_a = _vector_draw_call(vector_name, is_hook=True)
            block = _wrap_middle_or_subcut(
                "Hero fact-backed radial gauge stage",
                hero_a,
                f"const prog = eio(seg(lt, 0.08, Math.max(0.4, d * 0.85))) * {ratio};\n      K.drawRadialGauge(540, 670, 220, prog, {lbl_js}, {val_js}, eob(seg(lt, 0.10, 0.38)));",
                sfx_gain=0.55,
            )

        elif kind == "HAZARD_TWIST":
            stamp_js = json.dumps(cd["stamp"])
            banner_js = json.dumps(cd["banner"])
            hero_a = _vector_draw_call(vector_name, is_hook=False)
            block = _wrap_middle_or_subcut(
                "Word-synced impact stamp + bespoke hazard banner stage",
                hero_a,
                f"K.drawImpactStamp({stamp_js}, 540, 560, (lt > hit ? eob(seg(lt, hit, hit + 0.22)) : eob(seg(lt, 0.12, 0.36))) * 1.45);\n      K.drawHazardBanner({banner_js}, 540, 920, eob(seg(lt, 0.12, 0.4)));",
                sfx_gain=0.65,
            )

        elif kind.startswith("VECTOR_CALLOUT_"):
            ptr_js = json.dumps(cd["pointer_label"])
            sub_js = json.dumps(cd["sub_label"])
            mech_a = _vector_draw_call(vector_name, is_hook=False)
            mech_call = _vector_draw_call(vector_name, is_hook=True)
            block = _wrap_middle_or_subcut(
                "Annotated vector detail callout",
                mech_a,
                f"{mech_call}\n      K.drawBigStat({ptr_js}, {sub_js}, 540, 1050, lt > hit ? eob(seg(lt, hit, hit + 0.25)) : eob(seg(lt, 0.12, 0.42)));",
                sfx_gain=0.55,
            )

        else:  # METRIC_COMPARISON
            left_js = json.dumps(cd["left"])
            right_js = json.dumps(cd["right"])
            ratio = cd["ratio"]
            mech_a = _vector_draw_call(vector_name, is_hook=True)
            mech_call = _vector_draw_call(vector_name, is_hook=False)
            block = _wrap_middle_or_subcut(
                "Dynamic comparison bar + subject scene",
                mech_a,
                f"{mech_call}\n      K.drawComparisonBar(540, 1040, 820, 74, {ratio}, {left_js}, {right_js}, eob(seg(lt, 0.12, 0.4)));",
                sfx_gain=0.6,
            )

        shot_blocks.append(block)

    shots_body = "\n".join(shot_blocks)
    code = f"""// Auto-generated Per-Video 2D Motion Graphics Shots (Zero Boilerplate)
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
# 6. PER-VIDEO PROCEDURAL AUDIO MIXER GENERATOR (tools/mix.py)
# ═════════════════════════════════════════════════════════════════════════════

def build_music_config(
    theme_name: str,
    asset_seed: str,
    recent_assets: Optional[List[Dict[str, Any]]] = None,
    requested_mood: str = ""
) -> Dict[str, Any]:
    """Computes a fresh per-video music configuration distinct from the previous run."""
    recent_assets = recent_assets or []
    last_music = recent_assets[-1].get("music_config", {}) if recent_assets else {}

    seed_int = int(hashlib.sha256((asset_seed or theme_name).encode("utf-8")).hexdigest()[:8], 16)
    if requested_mood in ("bed", "tension", "ambient"):
        mode = requested_mood
    elif theme_name in ("HISTORIC_DOCUMENTARY", "SURVIVAL_TACTICAL"):
        mode = "tension" if (seed_int % 2 == 0) else "bed"
    else:
        mode = "ambient" if (seed_int % 2 == 0) else "bed"

    root_idx = seed_int % len(MUSIC_ROOT_POOL)
    root_hz = MUSIC_ROOT_POOL[root_idx]
    bpm = 74 + (seed_int % 5) * 4  # 74, 78, 82, 86, 90

    # Ensure immediate predecessor never shares identical (mode, root_hz, bpm)
    if (
        last_music.get("mode") == mode and
        last_music.get("root_hz") == root_hz and
        last_music.get("bpm") == bpm
    ):
        root_hz = MUSIC_ROOT_POOL[(root_idx + 1) % len(MUSIC_ROOT_POOL)]
        bpm = 74 + ((seed_int + 1) % 5) * 4

    return {
        "mode": mode,
        "root_hz": root_hz,
        "bpm": bpm,
        "music_seed": (seed_int % 99991) + 1,
    }


def generate_mix_py(music_config: Dict[str, Any]) -> str:
    """Generates a fresh per-video tools/mix.py parameterized by music_config."""
    default_seed = int(music_config.get("music_seed", 17))
    default_bpm = int(music_config.get("bpm", 82))
    default_root = float(music_config.get("root_hz", 220.0))

    return f'''"""Per-Video Procedural Audio Mixer: narration + soft sound effects + unique ambient music bed.
Generated freshly for this project. Keeps calm voice priority (-19 dBFS voice, -24 dB ducked music).
"""
import json, subprocess, sys
from pathlib import Path
import numpy as np
from scipy import signal
from scipy.io import wavfile

P = Path(sys.argv[1] if len(sys.argv) > 1 else '.')
SR = 48000
cj = json.loads((P / 'data/cues.json').read_text())
script = json.loads((P / 'script.json').read_text())
mc = script.get('music_config', {{}})
RNG_SEED = int(mc.get('music_seed', {default_seed}))
BPM = float(mc.get('bpm', {default_bpm}))
ROOT_HZ = float(mc.get('root_hz', {default_root}))
rng = np.random.default_rng(RNG_SEED)
DUR = float(cj['duration'])
N = int(DUR * SR) + SR // 10


def lp(x, f, o=2): b, a = signal.butter(o, min(f, SR / 2 - 100) / (SR / 2), 'low'); return signal.lfilter(b, a, x)
def bp(x, f0, f1, o=2): b, a = signal.butter(o, [f0 / (SR / 2), f1 / (SR / 2)], 'band'); return signal.lfilter(b, a, x)
def db(x): return 10 ** (x / 20)
def tt(d): return np.arange(int(d * SR)) / SR
def env(n, a=0.005, r=None):
    e = np.ones(n); na = max(1, int(a * SR)); e[:na] = np.linspace(0, 1, na)
    rest = n - na; e[na:] = np.exp(-np.linspace(0, r or 5, rest)) if rest > 0 else 1; return e
def sweep(f0, f1, d, shape='exp'):
    t = tt(d); f = f0 * (f1 / f0) ** (t / d) if shape == 'exp' else f0 + (f1 - f0) * t / d
    return np.sin(2 * np.pi * np.cumsum(f) / SR)
def noise(d): return rng.standard_normal(int(d * SR))


def whoosh(d=0.38, **_):
    n = noise(d); lo, hi = lp(n, 500), lp(n, 2200)
    k = np.sin(np.pi * np.linspace(0, 1, len(n))); x = (lo * (1 - k) + hi * k) * k ** 1.5
    return x / (np.abs(x).max() + 1e-9) * 0.5
def slide(d=1.0, **_):
    n = lp(noise(d), 700); e = np.sin(np.pi * np.linspace(0, 1, len(n))) ** 2
    return n / (np.abs(n).max() + 1e-9) * e * 0.35 + sweep(260, 120, d) * e * 0.08
def pop(**_): x = sweep(560, 240, 0.11) * env(int(0.11 * SR), 0.002, 6); return lp(x, 3000) * 0.7
def plop(**_): x = sweep(700, 180, 0.14) * env(int(0.14 * SR), 0.002, 5); return lp(x, 2500) * 0.6
def gulp(**_):
    a = sweep(320, 140, 0.16) * env(int(0.16 * SR), 0.01, 4); b = sweep(240, 90, 0.2) * env(int(0.2 * SR), 0.01, 4)
    x = np.concatenate([a, np.zeros(int(0.04 * SR)), b]); return lp(x, 1800) * 0.8
def boing(**_):
    d = 0.42; t = tt(d); f = 200 * (1 + 0.6 * t / d) * (1 + 0.08 * np.sin(2 * np.pi * 18 * t))
    return lp(np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.004, 4), 2000) * 0.55
def bubbles(d=1.2, **_):
    x = np.zeros(int(d * SR))
    for _ in range(int(d * 7)):
        st = rng.integers(0, max(1, len(x) - int(0.08 * SR))); f = rng.uniform(380, 900); b = sweep(f, f * 1.6, 0.06) * env(int(0.06 * SR), 0.003, 5)
        x[st:st + len(b)] += b * rng.uniform(0.2, 0.5)
    return lp(x, 2500) * 0.5
def sizzle(d=0.9, **_):
    n = bp(noise(d), 1800, 4500); crack = (rng.random(len(n)) < 0.002).astype(float); crack = lp(crack, 300) * 40
    e = np.minimum(1, np.linspace(0, 6, len(n))) * np.linspace(1, 0.2, len(n)); return n * (0.4 + crack) * e * 0.12
def sparkle(d=1.0, **_):
    notes = [784, 880, 1047, 1175, 1319, 1568]; x = np.zeros(int(d * SR) + SR // 2)
    for k, f in enumerate(notes):
        st = int(k * d / len(notes) * SR); n = int(0.4 * SR); t = tt(0.4)
        x[st:st + n] += (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)) * env(n, 0.004, 6) * 0.22
    return lp(x, 4500)
def thud(**_):
    d = 0.35; t = tt(d); x = np.sin(2 * np.pi * (70 + 40 * np.exp(-t * 30)) * t) * env(len(t), 0.002, 7)
    return x * 0.9 + lp(noise(d), 220) * env(len(t), 0.001, 12) * 0.3
def slam(**_):
    d = 0.45; t = tt(d); x = np.sin(2 * np.pi * (60 + 60 * np.exp(-t * 25)) * t) * env(len(t), 0.002, 6)
    return np.tanh(1.6 * (x + lp(noise(d), 1200) * env(len(t), 0.001, 10) * 0.6)) * 0.9
def tock(**_): d = 0.09; t = tt(d); return (np.sin(2 * np.pi * 420 * t) + 0.3 * np.sin(2 * np.pi * 840 * t)) * env(len(t), 0.001, 9) * 0.35
def zip_(**_):
    d = 0.32; n = bp(noise(d), 400, 3000); k = np.linspace(0, 1, len(n))
    return (n / (np.abs(n).max() + 1e-9) * 0.35 + sweep(300, 1100, d) * 0.12) * np.sin(np.pi * k) ** 1.2
def alarm(d=1.4, **_):
    x = np.zeros(int(d * SR)); one = np.sin(2 * np.pi * 150 * tt(0.22)) * env(int(0.22 * SR), 0.02, 5)
    for st in np.arange(0, max(0.1, d - 0.25), 0.5): i = int(st * SR); x[i:i + len(one)] += one
    return lp(x, 900) * 0.55
def inhale(d=1.0, **_):
    n = bp(noise(d), 300, 2600); k = np.linspace(0, 1, len(n)); e = np.sin(np.pi * np.minimum(1, k * 1.15)) ** 1.5 * (0.6 + 0.4 * k)
    return n / (np.abs(n).max() + 1e-9) * e * 0.5
def heartbeat(**_):
    one = lambda d, f: np.sin(2 * np.pi * f * tt(d)) * env(int(d * SR), 0.004, 7)
    x = np.concatenate([one(0.16, 58), np.zeros(int(0.09 * SR)), one(0.2, 52) * 0.75]); return lp(x, 300) * 1.0

FX = dict(inhale=inhale, heartbeat=heartbeat, whoosh=whoosh, slide=slide, pop=pop, plop=plop, gulp=gulp, boing=boing, bubbles=bubbles, sizzle=sizzle,
          sparkle=sparkle, thud=thud, slam=slam, tock=tock, zip=zip_, alarm=alarm)
LEVEL = dict(inhale=-17, heartbeat=-11, whoosh=-18, slide=-20, pop=-16, plop=-16, gulp=-13, boing=-17, bubbles=-21, sizzle=-19, sparkle=-18,
             thud=-13, slam=-11, tock=-19, zip=-16, alarm=-18)


def _transposed_chords(root_hz):
    ratios = [
        [1.0, 1.25, 1.5],
        [0.833, 1.0, 1.25],
        [0.667, 0.833, 1.0],
        [0.75, 0.9375, 1.125],
    ]
    return [[root_hz * r for r in ch] for ch in ratios]


def music_bed():
    beat = 60.0 / BPM; bar = beat * 4
    chords = _transposed_chords(ROOT_HZ)
    x = np.zeros(N)
    nb = int(np.ceil(DUR / bar)) + 1
    for b in range(nb):
        ch = chords[b % 4]; st = int(b * bar * SR); n = int(bar * SR)
        if st >= N: break
        t = tt(bar); e = np.minimum(1, t / 0.4) * np.minimum(1, (bar - t) / 0.4)
        pad = sum(np.sin(2 * np.pi * f / 2 * t) + 0.25 * np.sin(2 * np.pi * f * t) for f in ch) * e * 0.10
        x[st:st + n] += pad[:max(0, min(n, N - st))]
        for k in range(8):
            f = ch[[0, 1, 2, 1, 2, 0, 1, 2][k]] * (2 if k % 4 == 2 else 1); ps = st + int(k * beat / 2 * SR); pn = int(0.5 * SR)
            if ps + pn >= N: continue
            pt = tt(0.5); pl = (np.sin(2 * np.pi * f * pt) + 0.35 * np.sin(4 * np.pi * f * pt)) * env(pn, 0.003, 7) * 0.12
            x[ps:ps + pn] += pl
    x = lp(x, 3000)
    fade = np.ones(N); fi = min(N, int(0.12 * SR)); fo = min(N, int(0.20 * SR))
    if fi > 0: fade[:fi] *= np.linspace(0.35, 1, fi)
    if fo > 0: fade[-fo:] *= np.linspace(1, 0.25, fo)
    return x / (np.abs(x).max() + 1e-9) * fade


def music_tension():
    t = np.arange(N) / SR; x = np.zeros(N)
    base = ROOT_HZ * 0.25
    for mul, g in [(1.0, 0.5), (1.5, 0.3), (2.0, 0.2), (2.378, 0.12)]:
        x += np.sin(2 * np.pi * base * mul * t + np.sin(t * 0.35) * 0.5) * g
    x *= 0.55 + 0.45 * np.sin(2 * np.pi * t / 7.5) ** 2
    beat = 60.0 / BPM; ping = lambda f: (np.sin(2 * np.pi * f * tt(1.2)) + 0.3 * np.sin(4 * np.pi * f * tt(1.2))) * env(int(1.2 * SR), 0.01, 5)
    seq = [ROOT_HZ, ROOT_HZ * 1.189, ROOT_HZ * 0.891, ROOT_HZ * 0.794]
    for k in range(int(DUR / (beat * 2))):
        i = int(k * beat * 2 * SR); pg = ping(seq[(k // 2) % 4]) * 0.32
        if i + len(pg) < N: x[i:i + len(pg)] += pg
    x = lp(x, 2200)
    fade = np.ones(N); fi = min(N, int(0.12 * SR)); fo = min(N, int(0.22 * SR))
    if fi > 0: fade[:fi] *= np.linspace(0.35, 1, fi)
    if fo > 0: fade[-fo:] *= np.linspace(1, 0.25, fo)
    return x / (np.abs(x).max() + 1e-9) * fade


def music_ambient():
    t = np.arange(N) / SR; x = np.zeros(N)
    base = ROOT_HZ * 0.5
    for mul, g in [(1.0, 0.45), (1.498, 0.32), (2.0, 0.22), (2.245, 0.14)]:
        x += np.sin(2 * np.pi * base * mul * t + np.sin(t * 0.22 + mul) * 0.3) * g
    x = lp(x, 2400)
    fade = np.ones(N); fi = min(N, int(0.12 * SR)); fo = min(N, int(0.22 * SR))
    if fi > 0: fade[:fi] *= np.linspace(0.35, 1, fi)
    if fo > 0: fade[-fo:] *= np.linspace(1, 0.25, fo)
    return x / (np.abs(x).max() + 1e-9) * fade


def load_audio(f):
    out = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(f), '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-'], capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.float32).reshape(-1, 2).astype(np.float64)


mix = np.zeros((N, 2))
vf = P / 'data/narration.wav'
voice = None
if vf.exists():
    v = load_audio(vf)[:N]; voice = np.zeros((N, 2)); voice[:len(v)] = v
    rms = np.sqrt(np.mean(voice ** 2) + 1e-12); voice *= db(-19) / rms
    mix += voice
mus = script.get('music', 'bed')
if mus and mus != 'none':
    m = music_bed() if mus == 'bed' else music_tension() if mus == 'tension' else music_ambient() if mus == 'ambient' else None
    if m is None:
        a = load_audio(P / mus)[:N]; m = np.zeros(N); m[:len(a)] = a.mean(1); m /= np.abs(m).max() + 1e-9
    m = np.stack([m, m], 1) * db(-24 if voice is not None else -20)
    if voice is not None:
        lev = np.abs(voice.mean(1)); lev = signal.lfilter([1 - 0.9995], [1, -0.9995], lev); lev /= lev.max() + 1e-9
        m *= (1 - 0.55 * np.clip(lev * 3, 0, 1))[:, None]
    mix += m
for c in cj['cues']:
    fn = FX.get(c['type'])
    if not fn: continue
    x = fn(**({{'d': c['dur']}} if c.get('dur') else {{}}))
    x = lp(x, 5000) * db(LEVEL[c['type']]) * c.get('gain', 1.0) / (np.abs(x).max() + 1e-9) * 0.9
    i = int(c['t'] * SR); n = min(len(x), N - i)
    if n > 0 and i >= 0: pan = c.get('pan', 0.0); mix[i:i + n, 0] += x[:n] * (1 - max(0, pan)); mix[i:i + n, 1] += x[:n] * (1 + min(0, pan))
mix = np.tanh(mix * 1.2) / 1.2
mix *= db(-1) / (np.abs(mix).max() + 1e-9)
wavfile.write(P / 'data/mix.wav', SR, (mix * 32767).astype(np.int16))
print(f"data/mix.wav: {{DUR:.2f}} s · voice: {{'yes' if voice is not None else 'NO'}} · music: {{mus}} ({{BPM:.0f}} BPM @ {{ROOT_HZ:.1f}}Hz) · {{len(cj['cues'])}} cues")
'''


# ═════════════════════════════════════════════════════════════════════════════
# 7. MASTER 2D PROJECT SCAFFOLDER
# ═════════════════════════════════════════════════════════════════════════════

def scaffold_2d_project(
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
) -> Tuple[str, str, List[str]]:
    """Scaffolds a fresh per-video 2D project with unique assets and asset_manifest.json.

    Returns:
        (theme_name, palette_id, scene_sequence)
    """
    proj_dir = Path(proj_dir)
    proj_dir.mkdir(parents=True, exist_ok=True)

    theme_name = detect_topic_theme(topic, lines)
    palette = pick_variation_palette(theme_name, recent_palette_ids, variant_offset=variant_offset)
    seed = asset_seed or compute_asset_seed(run_id, topic, variant=variant_offset)
    m_cfg = music_config or build_music_config(theme_name, seed, recent_assets=recent_assets)

    inside_out_example = SKILL_DIR / "styles" / "inside-out" / "example"

    # Copy font & capture tool
    fonts_dir = proj_dir / "fonts"
    fonts_dir.mkdir(exist_ok=True)
    src_font = inside_out_example / "fonts" / "Inter-Black.otf"
    if src_font.exists():
        shutil.copy2(src_font, fonts_dir / "Inter-Black.otf")

    tools_dir = proj_dir / "tools"
    tools_dir.mkdir(exist_ok=True)
    src_cap = inside_out_example / "tools" / "capture.mjs"
    if src_cap.exists():
        shutil.copy2(src_cap, tools_dir / "capture.mjs")

    # Generate fresh per-video tools/mix.py
    mix_code = generate_mix_py(m_cfg)
    (tools_dir / "mix.py").write_text(mix_code, encoding="utf-8", newline="\n")

    # Scaffolding source directory
    src_dir = proj_dir / "src"
    src_dir.mkdir(exist_ok=True)
    core_dir = src_dir / "core"
    core_dir.mkdir(exist_ok=True)

    for core_file in ["lib.js", "timing.js", "captions.js"]:
        src = inside_out_example / "src" / "core" / core_file
        if src.exists():
            shutil.copy2(src, core_dir / core_file)

    # Write fresh kit2d.js
    kit2d_code = generate_kit2d_js(palette)
    (core_dir / "kit2d.js").write_text(kit2d_code, encoding="utf-8", newline="\n")

    # Compose bespoke zero-boilerplate storyboard and write shots.js
    plan = compose_video_visual_plan(
        title=title,
        topic=topic,
        lines=lines,
        theme=theme_name,
        asset_seed=seed,
        visual_plan=visual_plan,
    )
    shots_code, scene_sequence, focal_vector = generate_shots_js_from_plan(plan)
    (src_dir / "shots.js").write_text(shots_code, encoding="utf-8", newline="\n")

    # Write main.js complying fully with window.OP contract expected by tools/capture.mjs
    bg_color = palette.get("bg", "#0B1120")
    safe_title_html = json.dumps(title)[1:-1].replace("<", "&lt;").replace(">", "&gt;")
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
  const punch = 1 + 0.11 * (1 - eo(clamp(lt / 0.28)));
  const drift = 1 + (sh.zoom ?? 0.06) * eio(clamp(lt / d));
  const [cx, cy] = sh.cam || [540, 740];
  ctx.save(); ctx.translate(cx, cy); ctx.scale(punch * drift, punch * drift); ctx.translate(-cx, -cy);
  sh.draw(lt, d, t);
  ctx.restore();
  ctx.globalAlpha = 1; ctx.letterSpacing = '0px';
  if (i > 0 && lt < 0.09) {{ ctx.fillStyle = '#FFFFFF'; ctx.globalAlpha = 0.35 * (1 - lt / 0.09); ctx.fillRect(0, 0, W, H); ctx.globalAlpha = 1; }}
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
    (src_dir / "main.js").write_text(main_code, encoding="utf-8", newline="\n")

    html_code = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{safe_title_html}</title>
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
    (proj_dir / "index.html").write_text(html_code, encoding="utf-8", newline="\n")

    # Write per-video asset_manifest.json for Gate 3B freshness & provenance verification
    manifest = {
        "run_id": str(run_id),
        "asset_seed": seed,
        "project_dir_name": proj_dir.name,
        "title": title,
        "topic": topic,
        "theme": theme_name,
        "style": "2d-motion",
        "palette_id": palette["id"],
        "focal_vector": focal_vector,
        "has_subcuts": any(sp.get("has_subcut") for sp in plan.get("shots", [])),
        "scene_sequence": scene_sequence,
        "background_sequence": plan["background_sequence"],
        "card_texts": plan["card_texts"],
        "music_config": m_cfg,
        "shots_sha256": compute_text_sha256(shots_code),
        "file_hashes": {
            "src/core/kit2d.js": compute_text_sha256(kit2d_code),
            "src/shots.js": compute_text_sha256(shots_code),
            "src/main.js": compute_text_sha256(main_code),
            "tools/mix.py": compute_text_sha256(mix_code),
            "index.html": compute_text_sha256(html_code),
        },
    }
    (proj_dir / "asset_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
        newline="\n"
    )

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

    last_entry = history_entries[-1]
    if (
        last_entry.get("theme") == theme_name and
        last_entry.get("palette") == palette_id and
        last_entry.get("scene_sequence") == scene_sequence
    ):
        return False, f"Visual stagnation: Planned video matches immediate predecessor theme ({theme_name}), palette ({palette_id}), and scene sequence."

    return True, f"Visual composition approved ({theme_name}, {palette_id})."
