import re
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from build_templates import generate_setting_file
from core.styles import STYLES
from core.transcriber import CaptionSegment
from core.xml_generator import generate_fcpxml


class StyleCatalogTests(unittest.TestCase):
    def test_generated_variants_have_unique_animated_fusion_templates(self):
        variants = {
            name: style["template_config"]
            for name, style in STYLES.items()
            if "template_config" in style
        }

        self.assertGreaterEqual(len(STYLES), 50)
        names = [style["name"] for style in STYLES.values()]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(len(variants), 64)

        tool_ids = set()
        for name, config in variants.items():
            safe_tool_id = re.sub(r"[^A-Za-z0-9_]", "", name)
            content = generate_setting_file(name, config)
            self.assertTrue(config["animated"], name)
            self.assertNotIn(safe_tool_id, tool_ids)
            self.assertIn("GroupOperator", content, name)
            self.assertIn("KeyStretcher", content, name)
            self.assertIn(f'ActiveTool = "{safe_tool_id}"', content, name)
            tool_ids.add(safe_tool_id)

    def test_caption_xml_animates_generated_text_with_a_pop_in(self):
        segment = CaptionSegment(1, 0.0, 1.0, "VIRAL CAPTION", [])
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "captions.fcpxml"
            generate_fcpxml([segment], str(output_path), style_name="Viral Pop - Lemon")
            title = ET.parse(output_path).find(".//title")

        self.assertIsNotNone(title)
        keyframes = title.findall("./adjust-transform/param[@name='scale']/keyframe")
        self.assertEqual(len(keyframes), 3)
        self.assertEqual(keyframes[0].get("value"), "0.82 0.82")
        self.assertEqual(keyframes[1].get("value"), "1.08 1.08")
        self.assertEqual(keyframes[2].get("value"), "1 1")

    def test_every_catalog_style_animates_generated_caption_text(self):
        segment = CaptionSegment(1, 0.0, 1.0, "ANIMATED CAPTION", [])
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "captions.fcpxml"
            for style_name in STYLES:
                generate_fcpxml([segment], str(output_path), style_name=style_name)
                title = ET.parse(output_path).find(".//title")
                self.assertIsNotNone(title, style_name)
                keyframes = title.findall("./adjust-transform/param[@name='scale']/keyframe")
                self.assertEqual(len(keyframes), 3, style_name)


if __name__ == "__main__":
    unittest.main()
