"""Unit tests for cloud.style_router and cloud.visual_engine_2d."""
import ast
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from cloud.style_router import scaffold_styled_project, select_visual_style
from cloud.visual_engine_2d import (
    build_music_config,
    compose_video_visual_plan,
    detect_topic_focal_vector,
    detect_topic_theme,
    generate_kit2d_js,
    generate_mix_py,
    generate_shots_js_from_plan,
    pick_variation_palette,
)


class TestVisualAndStyleUnit(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="unit_vis_"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_select_visual_style_rotates_on_repeat(self):
        self.assertEqual(select_visual_style("t", [], "HISTORIC_DOCUMENTARY"), "paper-atlas")
        self.assertEqual(
            select_visual_style("t", [], "HISTORIC_DOCUMENTARY", recent_assets=[{"style": "paper-atlas"}]),
            "2d-motion",
        )
        self.assertEqual(select_visual_style("t", [], "SURVIVAL_TACTICAL"), "stick-story")
        self.assertEqual(
            select_visual_style("t", [], "SURVIVAL_TACTICAL", recent_assets=[{"style": "stick-story"}]),
            "2d-motion",
        )

    def test_visual_engine_plan_kit_shots_and_mix_syntax(self):
        lines = [
            {"text": "Why do neutron stars spin hundreds of times per second?", "caps": "Neutron *stars"},
            {"text": "Conservation of angular momentum speeds up the collapsing core.", "caps": "Angular *momentum"},
            {"text": "A city-sized sphere spins faster than a blender blade.", "caps": "City-sized *sphere", "gap": 0.2},
        ]
        theme = detect_topic_theme("neutron star spin", lines)
        self.assertEqual(theme, "COSMIC_SPACE")
        vec, _, _ = detect_topic_focal_vector("neutron star spin", lines)
        self.assertTrue(bool(vec))

        palette = pick_variation_palette(theme, [])
        plan = compose_video_visual_plan("Neutron Stars #shorts", "neutron star spin", lines, theme, asset_seed="seed-1")
        shots_js, seq, fv = generate_shots_js_from_plan(plan)
        self.assertIn("export function buildShots()", shots_js)
        self.assertGreaterEqual(len(seq), len(lines))
        self.assertTrue(bool(fv))

        kit_js = generate_kit2d_js(palette)
        self.assertIn("export const P =", kit_js)

        m_cfg = build_music_config(theme, "seed-1")
        mix_py = generate_mix_py(m_cfg)
        ast.parse(mix_py)  # Must be valid Python syntax

    def test_scaffold_all_three_styles_and_node_check_js(self):
        has_node = shutil.which("node") is not None
        self.assertTrue(has_node, "Node.js required for JS syntax checks")

        cases = [
            ("2d-motion", "Black Hole Gravity #shorts", "black hole event horizon"),
            ("paper-atlas", "The 1919 Molasses Flood #shorts", "1919 boston harbor molasses ship flood"),
            ("stick-story", "How to Survive an Avalanche #shorts", "surviving a snow avalanche burial"),
        ]
        for idx, (style, title, topic) in enumerate(cases):
            with self.subTest(style=style):
                pdir = self.tmp / f"proj_{idx}"
                lines = [
                    {"text": f"What happens during {topic}?", "caps": "What *happens"},
                    {"text": "Pressure rises rapidly while every second counts for survival.", "caps": "Pressure *rises"},
                    {"text": "One calm decision changes the final outcome.", "caps": "Calm *decision", "gap": 0.2},
                ]
                _, _, _, chosen = scaffold_styled_project(
                    proj_dir=pdir,
                    title=title,
                    topic=topic,
                    lines=lines,
                    recent_palette_ids=[],
                    run_id=f"u-{idx}",
                    requested_style=style,
                )
                self.assertEqual(chosen, style)
                ast.parse((pdir / "tools" / "mix.py").read_text(encoding="utf-8"))
                kit_rel = "src/core/kit2d.js" if style == "2d-motion" else "src/core/kit.js"
                for rel in [kit_rel, "src/shots.js", "src/main.js"]:
                    res = subprocess.run(["node", "--check", str(pdir / rel)], capture_output=True, text=True)
                    self.assertEqual(res.returncode, 0, f"{style} {rel} syntax error: {res.stderr}")


if __name__ == "__main__":
    unittest.main()
