"""
solid-description: Unit tests for load_detection_rules tool. Tests verify that a
principle whose rule.md has XML blocks returns structured per-metric instructions,
a principle without XML blocks returns full_content, unknown principles return error,
and matched_tags reduces the returned principle count.
solid-category: unit-test
"""

import unittest
from tests.helpers import make_handler


class TestLoadDetectionRules(unittest.TestCase):
    def setUp(self):
        self.handler = make_handler()

    def test_srp_with_xml_blocks_returns_structured_detection_dict(self):
        result = self.handler.load_detection_rules(principle="srp")
        p = result["principles"][0]
        self.assertIn("detection", p)
        self.assertIsInstance(p["detection"], dict)

    def test_srp_with_xml_blocks_returns_structured_definition_dict(self):
        result = self.handler.load_detection_rules(principle="srp")
        p = result["principles"][0]
        self.assertIn("definition", p)
        self.assertIsInstance(p["definition"], dict)

    def test_isp_without_xml_blocks_returns_full_content_key(self):
        result = self.handler.load_detection_rules(principle="isp")
        p = result["principles"][0]
        self.assertIn("full_content", p)

    def test_isp_without_xml_blocks_full_content_is_nonempty_string(self):
        result = self.handler.load_detection_rules(principle="isp")
        p = result["principles"][0]
        full_content = p.get("full_content", "")
        self.assertIsInstance(full_content, str)
        self.assertGreater(len(full_content), 0)

    def test_unknown_principle_returns_error(self):
        result = self.handler.load_detection_rules(principle="nonexistent_xyz_principle")
        self.assertIn("error", result)

    def test_no_argument_returns_multiple_principles(self):
        result = self.handler.load_detection_rules()
        self.assertGreater(len(result.get("principles", [])), 0)

    def test_matched_tags_returns_fewer_principles_than_unfiltered(self):
        unfiltered = self.handler.load_detection_rules()
        tag_filtered = self.handler.load_detection_rules(matched_tags=["unit-test"])
        self.assertLess(
            len(tag_filtered.get("principles", [])),
            len(unfiltered.get("principles", [])),
        )


if __name__ == "__main__":
    unittest.main()
