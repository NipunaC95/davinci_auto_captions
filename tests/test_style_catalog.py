import re
import unittest

from build_templates import generate_setting_file
from core.styles import STYLES


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


if __name__ == "__main__":
    unittest.main()
