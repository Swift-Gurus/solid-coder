"""Tests for mcp-server/rule_stripper.py — review-content stripping for rule.md."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "mcp-server"))
import rule_stripper  # noqa: E402


class TestStripH2Sections(unittest.TestCase):
    def test_removes_named_section(self):
        text = (
            "# Title\n\n"
            "## Rule\nkeep me\n\n"
            "## Quantitative Metrics Summary\n"
            "| col | col |\n"
            "|---|---|\n"
            "| bad | stuff |\n\n"
            "## Exceptions\nkeep this too\n"
        )
        out = rule_stripper.strip_h2_sections(text, ["Quantitative Metrics Summary"])
        self.assertNotIn("Quantitative Metrics Summary", out)
        self.assertNotIn("bad | stuff", out)
        self.assertIn("keep me", out)
        self.assertIn("keep this too", out)

    def test_empty_names_is_noop(self):
        text = "## One\nx\n## Two\ny\n"
        self.assertEqual(rule_stripper.strip_h2_sections(text, []), text)

    def test_section_extending_to_eof(self):
        text = "## Keep\ndata\n\n## Drop\nremove all\nthis too\n"
        out = rule_stripper.strip_h2_sections(text, ["Drop"])
        self.assertIn("data", out)
        self.assertNotIn("Drop", out)
        self.assertNotIn("remove all", out)


class TestStripBoldSubsections(unittest.TestCase):
    def test_removes_detection_block(self):
        text = (
            "### SC-1: Rule Name\n\n"
            "A type MUST use one concurrency model.\n\n"
            "**Detection:**\n\n"
            "1. Count async functions\n"
            "2. Count GCD calls\n\n"
            "**Rationale:**\n\n"
            "Mixing models is unpredictable.\n"
        )
        out = rule_stripper.strip_bold_subsections(text, ["Detection"])
        self.assertNotIn("**Detection:**", out)
        self.assertNotIn("Count async functions", out)
        self.assertIn("MUST use one concurrency model", out)
        self.assertIn("**Rationale:**", out)
        self.assertIn("unpredictable", out)

    def test_stops_at_next_header(self):
        text = (
            "### SC-1: Rule\nprose\n\n"
            "**Detection:**\n\n"
            "strip this\n\n"
            "### SC-2: Next Rule\nkeep\n"
        )
        out = rule_stripper.strip_bold_subsections(text, ["Detection"])
        self.assertNotIn("strip this", out)
        self.assertIn("### SC-2: Next Rule", out)
        self.assertIn("keep", out)

    def test_multiple_labels(self):
        text = (
            "**Detection:**\nd\n\n"
            "**Analysis:**\na\n\n"
            "**Keep:**\nk\n"
        )
        out = rule_stripper.strip_bold_subsections(text, ["Detection", "Analysis"])
        self.assertNotIn("Detection", out)
        self.assertNotIn("Analysis", out)
        self.assertIn("**Keep:**", out)
        self.assertIn("k", out)

    def test_empty_labels_is_noop(self):
        text = "**Detection:**\nkeep me now\n"
        self.assertEqual(rule_stripper.strip_bold_subsections(text, []), text)


class TestStripReviewContent(unittest.TestCase):
    def test_combined_strip(self):
        text = (
            "# Principle X\n\n"
            "Intro prose.\n\n"
            "## Metrics:\n\n"
            "### X-1: First Rule\n\n"
            "Prose about the rule.\n\n"
            "**Detection:**\n\n"
            "1. Count foo\n\n"
            "**Result:**\n\n"
            "| col | col |\n"
            "|---|---|\n\n"
            "## Quantitative Metrics Summary\n\n"
            "| ID | Severity |\n"
            "|----|----------|\n"
        )
        out = rule_stripper.strip_review_content(
            text,
            h2_sections=["Quantitative Metrics Summary"],
            bold_subsections=["Detection", "Result"],
        )
        self.assertIn("# Principle X", out)
        self.assertIn("Intro prose", out)
        self.assertIn("### X-1: First Rule", out)
        self.assertIn("Prose about the rule", out)
        self.assertNotIn("**Detection:**", out)
        self.assertNotIn("Count foo", out)
        self.assertNotIn("**Result:**", out)
        self.assertNotIn("Quantitative Metrics Summary", out)

    def test_idempotent(self):
        text = "## Quantitative Metrics Summary\nx\n"
        once = rule_stripper.strip_review_content(text, ["Quantitative Metrics Summary"], [])
        twice = rule_stripper.strip_review_content(once, ["Quantitative Metrics Summary"], [])
        self.assertEqual(once, twice)


if __name__ == "__main__":
    unittest.main()
