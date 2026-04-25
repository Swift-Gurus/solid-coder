"""Tests for mcp-server/docs/server.py"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "mcp-server"))
sys.path.insert(0, str(ROOT / "mcp-server" / "docs"))

import importlib.util
spec = importlib.util.spec_from_file_location(
    "docs_server", ROOT / "mcp-server" / "docs" / "server.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class TestGetCandidateTags(unittest.TestCase):
    def test_returns_dict_with_tags(self):
        result = mod.get_candidate_tags()
        self.assertIn("candidate_tags", result)
        self.assertIsInstance(result["candidate_tags"], list)

    def test_tags_are_strings(self):
        result = mod.get_candidate_tags()
        for tag in result["candidate_tags"]:
            self.assertIsInstance(tag, str)


class TestLoadRules(unittest.TestCase):
    def test_code_mode_returns_string(self):
        result = mod.load_rules(mode="code")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_planner_mode_returns_string(self):
        result = mod.load_rules(mode="planner")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_synth_fixes_mode_returns_string(self):
        result = mod.load_rules(mode="synth-fixes")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_synth_impl_mode_returns_string(self):
        result = mod.load_rules(mode="synth-impl")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_review_mode_with_principle(self):
        result = mod.load_rules(mode="review", principle="SRP")
        self.assertIsInstance(result, str)
        self.assertIn("SRP", result)

    def test_single_principle_narrows_output(self):
        one_result = mod.load_rules(mode="planner", principle="SRP")
        # Single principle must contain SRP content and not mention OCP at top level
        self.assertIn("SRP", one_result)
        # Must not load all principles (either OCP absent, or output is chunked file list)
        is_chunked = "Read each file" in one_result
        if not is_chunked:
            self.assertNotIn("# OCP", one_result)

    def test_unknown_mode_returns_error(self):
        result = mod.load_rules(mode="nonexistent-mode")
        self.assertIn("Error", result)

    def test_unknown_principle_returns_not_found(self):
        result = mod.load_rules(mode="code", principle="NOTAPRINCIPLE")
        self.assertIn("not found", result.lower())

    def test_no_yaml_frontmatter_in_output(self):
        result = mod.load_rules(mode="planner", principle="SRP")
        # Output must start with our # SRP header, not raw frontmatter
        lines = result.splitlines()
        self.assertTrue(lines[0].startswith("#"), f"First line should be a header, got: {lines[0]!r}")
        # Frontmatter field "name: ..." should not appear as a bare YAML key at line start
        self.assertNotIn("\nname: Single Responsibility", result)
        self.assertNotIn("\nname: SRP", result)

    def test_matched_tags_filters_conditional_principles(self):
        all_result = mod.load_rules(mode="code", matched_tags=None)
        # swiftui tag loads SwiftUI principle; empty list should not error
        tagged_result = mod.load_rules(mode="code", matched_tags=[])
        self.assertIsInstance(tagged_result, str)

    def test_output_contains_principle_header(self):
        result = mod.load_rules(mode="planner", principle="SRP")
        self.assertIn("# SRP", result)


class TestLoadExamples(unittest.TestCase):
    def test_srp_examples_returned(self):
        result = mod.load_examples(principle="SRP")
        self.assertIn("SRP", result)
        self.assertIn("```swift", result)

    def test_examples_labeled_compliant_or_violation(self):
        result = mod.load_examples(principle="SRP")
        self.assertTrue("[compliant]" in result or "[violation]" in result)

    def test_unknown_principle_returns_available_list(self):
        result = mod.load_examples(principle="NOTEXIST")
        self.assertIn("not found", result.lower())
        self.assertIn("Available", result)

    def test_ocp_examples_returned(self):
        result = mod.load_examples(principle="OCP")
        self.assertIn("OCP", result)
        self.assertIn("```swift", result)


class TestLoadPattern(unittest.TestCase):
    def test_strategy_pattern_found(self):
        result = mod.load_pattern(name="strategy")
        self.assertIn("Strategy", result)
        self.assertNotIn("not found", result.lower())

    def test_facade_pattern_found(self):
        result = mod.load_pattern(name="facade")
        self.assertIn("Facade", result)

    def test_unknown_pattern_returns_catalog(self):
        result = mod.load_pattern(name="nonexistent-pattern")
        self.assertIn("not found", result.lower())
        self.assertIn("Available patterns", result)
        self.assertIn("strategy", result.lower())

    def test_case_insensitive_lookup(self):
        lower = mod.load_pattern(name="strategy")
        upper = mod.load_pattern(name="Strategy")
        self.assertEqual(lower, upper)

    def test_no_frontmatter_in_pattern(self):
        result = mod.load_pattern(name="strategy")
        # Content should not start with frontmatter block
        self.assertFalse(result.startswith("---"))


class TestSeverityStripping(unittest.TestCase):
    def _planner_srp(self):
        return mod.load_rules(mode="planner", principle="SRP")

    def _review_srp(self):
        return mod.load_rules(mode="review", principle="SRP")

    def test_non_review_strips_severity_bands_heading(self):
        result = self._planner_srp()
        self.assertNotIn("Severity Bands", result)

    def test_non_review_strips_quantitative_summary_heading(self):
        result = self._planner_srp()
        self.assertNotIn("Quantitative Metrics Summary", result)

    def test_non_review_strips_severity_band_bullets(self):
        result = self._planner_srp()
        # ✅/⚠️/🔥 bullets and MINOR only appear in Severity Bands, not in Exceptions
        self.assertNotIn("⚠️", result)
        self.assertNotIn("🔥 **SEVERE**", result)
        self.assertNotIn("✅ **COMPLIANT**", result)
        # MINOR as a standalone severity label is unique to the Severity Bands section
        self.assertNotIn("**MINOR**", result)

    def test_non_review_keeps_metric_detection_sections(self):
        result = self._planner_srp()
        # SRP-1, SRP-2, SRP-3 describe what violations are — must stay
        self.assertIn("SRP-1", result)
        self.assertIn("SRP-2", result)

    def test_non_review_keeps_exceptions_section(self):
        result = self._planner_srp()
        self.assertIn("Exceptions", result)

    def test_review_mode_keeps_severity_bands(self):
        result = self._review_srp()
        self.assertIn("Severity Bands", result)

    def test_review_mode_keeps_quantitative_summary(self):
        result = self._review_srp()
        self.assertIn("Quantitative Metrics Summary", result)

    def test_review_mode_keeps_severity_bullets(self):
        result = self._review_srp()
        self.assertIn("COMPLIANT", result)

    def test_strip_helper_directly(self):
        sample = (
            "## Detection\n\ncount things\n\n"
            "### Exceptions(NOT violations):\n- facade\n\n"
            "### Severity Bands:\n- ✅ COMPLIANT\n- 🔥 SEVERE\n---\n\n"
            "## Quantitative Metrics Summary\n| col |\n|---|\n| val |\n---\n\n"
            "## Other Section\n\nsome content\n"
        )
        result = mod._strip_review_only_sections(sample)
        self.assertIn("Detection", result)
        self.assertIn("Exceptions", result)
        self.assertIn("Other Section", result)
        self.assertNotIn("Severity Bands", result)
        self.assertNotIn("Quantitative Metrics Summary", result)
        self.assertNotIn("COMPLIANT", result)
        self.assertNotIn("SEVERE", result)

    def test_strip_preserves_content_after_summary(self):
        sample = (
            "## Quantitative Metrics Summary\n| x |\n---\n\n"
            "## Still Here\n\nthis stays\n"
        )
        result = mod._strip_review_only_sections(sample)
        self.assertIn("Still Here", result)
        self.assertIn("this stays", result)

    def test_synth_fixes_strips_severity_bands(self):
        result = mod.load_rules(mode="synth-fixes", principle="OCP")
        self.assertNotIn("Severity Bands", result)
        self.assertNotIn("Quantitative Metrics Summary", result)

    def test_synth_impl_strips_severity_bands(self):
        result = mod.load_rules(mode="synth-impl", principle="OCP")
        self.assertNotIn("Severity Bands", result)


if __name__ == "__main__":
    unittest.main()
