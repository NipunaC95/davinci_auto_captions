import re
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from build_templates import TEMPLATES, generate_setting_file
from core.styles import ANIMATION_PRESETS, STYLES
from core.timeline_injector import _write_overlay_timeline_xml
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
        animation_types = set()
        for name, config in variants.items():
            safe_tool_id = re.sub(r"[^A-Za-z0-9_]", "", name)
            content = generate_setting_file(name, config)
            self.assertTrue(config["animated"], name)
            self.assertIn(config["animation"], ANIMATION_PRESETS, name)
            animation_types.add(config["animation"])
            self.assertNotIn(safe_tool_id, tool_ids)
            self.assertIn("GroupOperator", content, name)
            self.assertIn("KeyStretcher", content, name)
            self.assertIn("AnimTransform = Transform", content, name)
            self.assertIn("FadeMerge = Merge", content, name)
            self.assertIn("AnimSizeSpline = BezierSpline", content, name)
            self.assertIn("AnimOpacitySpline = BezierSpline", content, name)
            self.assertIn(f'ActiveTool = "{safe_tool_id}"', content, name)
            tool_ids.add(safe_tool_id)

        self.assertEqual(len(animation_types), 8)

    def test_all_templates_include_expected_motion_modifiers(self):
        self.assertEqual(len(TEMPLATES), len(STYLES))
        comic_template = generate_setting_file("Retro Comic Pop", TEMPLATES["Retro Comic Pop"])
        self.assertIn("AnimAngleSpline = BezierSpline", comic_template)

        slide_template = generate_setting_file("Cinematic Box", TEMPLATES["Cinematic Box"])
        self.assertIn("AnimCenterPath = XYPath", slide_template)
        self.assertIn("AnimCenterY = BezierSpline", slide_template)

    def test_caption_xml_animates_generated_text_with_valid_keyframe_animation(self):
        segment = CaptionSegment(1, 0.0, 1.0, "VIRAL CAPTION", [])
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "captions.fcpxml"
            generate_fcpxml([segment], str(output_path), style_name="Viral Pop - Lemon")
            title = ET.parse(output_path).find(".//title")

        self.assertIsNotNone(title)
        keyframes = title.findall("./adjust-transform/param[@name='scale']/keyframeAnimation/keyframe")
        self.assertEqual(len(keyframes), 4)
        self.assertEqual(keyframes[0].get("value"), "0.55 0.55")
        self.assertEqual(keyframes[1].get("value"), "1.16 1.16")
        self.assertEqual(keyframes[2].get("value"), "0.97 0.97")
        self.assertEqual(keyframes[3].get("value"), "1 1")

        opacity_keyframes = title.findall("./adjust-blend/param[@name='amount']/keyframeAnimation/keyframe")
        self.assertEqual(len(opacity_keyframes), 2)

    def test_every_catalog_style_animates_generated_caption_text(self):
        segment = CaptionSegment(1, 0.0, 1.0, "ANIMATED CAPTION", [])
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "captions.fcpxml"
            for style_name, style in STYLES.items():
                generate_fcpxml([segment], str(output_path), style_name=style_name)
                title = ET.parse(output_path).find(".//title")
                self.assertIsNotNone(title, style_name)
                keyframes = title.findall("./adjust-transform/param[@name='scale']/keyframeAnimation/keyframe")
                expected_count = len(ANIMATION_PRESETS[style["animation"]]["scale"])
                self.assertEqual(len(keyframes), expected_count, style_name)

    def test_short_clip_scales_keyframes_without_duplicate_timestamps(self):
        segment = CaptionSegment(1, 0.0, 0.2, "FAST", [])
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "short.fcpxml"
            generate_fcpxml([segment], str(output_path), fps=30.0, style_name="MrBeast Highlighter")
            title = ET.parse(output_path).find(".//title")

        self.assertIsNotNone(title)
        times = [
            kf.get("time")
            for kf in title.findall("./adjust-transform/param[@name='scale']/keyframeAnimation/keyframe")
        ]
        self.assertGreaterEqual(len(times), 2)
        self.assertEqual(len(times), len(set(times)))

    def test_overlay_preserves_existing_captions_and_stacks_on_top_lane(self):
        source_xml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE fcpxml>
<fcpxml version="1.9">
  <resources>
    <format id="r1" name="FFVideoFormat1080p30" frameDuration="1/30s" width="1920" height="1080"/>
    <effect id="r_orig" name="Basic Title" uid=".../Basic Title.moti"/>
    <asset id="r_vid" name="clip.mp4" start="0s" duration="5s"/>
  </resources>
  <library>
    <event name="Timeline">
      <project name="Timeline">
        <sequence format="r1" duration="5s" tcStart="0s">
          <spine>
            <asset-clip ref="r_vid" offset="0s" start="10s" duration="5s">
              <title ref="r_orig" lane="1" offset="10s" duration="2s" name="ORIGINAL CAPTION">
                <text><text-style ref="orig1">ORIGINAL CAPTION</text-style></text>
                <text-style-def id="orig1"><text-style font="Arial" fontSize="48"/></text-style-def>
              </title>
            </asset-clip>
          </spine>
        </sequence>
      </project>
    </event>
  </library>
</fcpxml>
"""
        segment = CaptionSegment(1, 0.5, 2.5, "NEW CAPTION", [])
        with tempfile.TemporaryDirectory() as directory:
            source_path = Path(directory) / "source.fcpxml"
            captions_path = Path(directory) / "captions.fcpxml"
            merged_path = Path(directory) / "merged.fcpxml"
            source_path.write_text(source_xml, encoding="utf-8")
            generate_fcpxml([segment], str(captions_path), style_name="Hormozi Viral")
            _write_overlay_timeline_xml(
                str(source_path),
                str(captions_path),
                str(merged_path),
                "Timeline_with_Captions",
            )
            clip = ET.parse(merged_path).find(".//spine/asset-clip")

        self.assertIsNotNone(clip)
        titles = clip.findall("./title")
        self.assertEqual(len(titles), 2)
        self.assertEqual(titles[0].get("name"), "ORIGINAL CAPTION")
        self.assertEqual(titles[0].get("lane"), "1")
        self.assertEqual(titles[1].get("name"), "NEW CAPTION")
        self.assertEqual(titles[1].get("lane"), "2")
        self.assertEqual(titles[1].get("offset"), "21/2s")


if __name__ == "__main__":
    unittest.main()
