"""
solid-description: Verifies that the detection rule loader returns structured principle data for valid inputs, errors for unknown principles, and respects tag-based filtering to narrow the result set.
solid-category: unit-test
"""

import unittest
from tests.helpers import make_handler


class TestLoadDetectionRules(unittest.TestCase):
    def setUp(self):
        self.handler = make_handler()

    def _load_first_principle(self, name: str) -> dict:
        return self.handler.load_detection_rules(principle=name)["principles"][0]

    def test_srp_with_xml_blocks_returns_structured_detection_dict(self):
        p = self._load_first_principle("srp")
        self.assertIn("detection", p)
        self.assertIsInstance(p["detection"], dict)

    def test_srp_with_xml_blocks_returns_structured_definition_dict(self):
        p = self._load_first_principle("srp")
        self.assertIn("definition", p)
        self.assertIsInstance(p["definition"], dict)

    def test_isp_with_xml_blocks_returns_detection_key(self):
        p = self._load_first_principle("isp")
        self.assertIn("detection", p)
        self.assertIsInstance(p["detection"], dict)

    def test_isp_with_xml_blocks_returns_severity_bands_field(self):
        """severity_bands field is present but empty — bands are now in YAML frontmatter."""
        p = self._load_first_principle("isp")
        self.assertIn("severity_bands", p)
        self.assertEqual(p["severity_bands"], {},
                         "severity_bands XML blocks removed — scoring uses YAML frontmatter bands")

    def test_unknown_principle_returns_error(self):
        result = self.handler.load_detection_rules(principle="nonexistent_xyz_principle")
        self.assertIn("error", result)

    def test_no_argument_returns_multiple_principles(self):
        result = self.handler.load_detection_rules()
        self.assertGreater(len(result.get("principles", [])), 0)

    def test_matched_tags_returns_fewer_principles_than_unfiltered(self):
        unfiltered = self.handler.load_detection_rules()
        tag_filtered = self.handler.load_detection_rules(matched_tags=["unit-test"])
        unfiltered_count = len(unfiltered.get("principles", []))
        filtered_count = len(tag_filtered.get("principles", []))
        # "unit-test" activates the Unit Testing principle + always-on principles.
        # Conditional principles without a matching tag are excluded,
        # so the filtered set must be smaller than the full unfiltered set.
        self.assertGreater(filtered_count, 0, "tag filter returned no principles")
        self.assertLess(filtered_count, unfiltered_count)


    def test_fallback_path_returns_content_not_full_content(self):
        # code-smells has no XML blocks — hits the fallback path.
        # The fallback must NOT expose a full_content key; only content.
        p = self._load_first_principle("code-smells")
        self.assertIn("content", p)
        self.assertNotIn("full_content", p)


if __name__ == "__main__":
    unittest.main()
