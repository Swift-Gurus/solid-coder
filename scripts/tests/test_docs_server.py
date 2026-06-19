"""Tests for mcp-server/docs/server.py"""
import json
import sys
import tempfile
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
        self.assertIn("<exceptions>", result)

    def test_review_mode_keeps_severity_bands(self):
        result = self._review_srp()
        self.assertIn("<severity-bands", result)

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


class TestLoadFixForViolation(unittest.TestCase):
    def test_known_metric_returns_content(self):
        result = mod.load_fix_for_violation("OCP-1")
        self.assertIsInstance(result, str)
        self.assertIn("OCP-1", result)
        self.assertGreater(len(result), 50)

    def test_metric_id_case_insensitive(self):
        lower = mod.load_fix_for_violation("ocp-1")
        upper = mod.load_fix_for_violation("OCP-1")
        self.assertEqual(lower, upper)

    def test_unknown_metric_returns_error_string(self):
        result = mod.load_fix_for_violation("OCP-99")
        self.assertIn("OCP-99", result)
        self.assertIn("Available", result)

    def test_completely_unknown_metric_returns_error(self):
        result = mod.load_fix_for_violation("BOGUS-99")
        self.assertIn("BOGUS-99", result)
        self.assertIn("Available", result)

    def test_no_frontmatter_in_output(self):
        result = mod.load_fix_for_violation("LSP-1")
        self.assertFalse(result.startswith("---"))

    def test_output_contains_header(self):
        result = mod.load_fix_for_violation("LSP-3")
        self.assertTrue(result.startswith("# LSP"))

    def test_all_core_metrics_resolve(self):
        for metric_id in [
            "SRP-1", "SRP-2", "SRP-3",
            "OCP-1", "OCP-2",
            "LSP-1", "LSP-2", "LSP-3",
            "ISP-1", "ISP-2", "ISP-3",
            "DRY-1", "DRY-2", "DRY-3",
        ]:
            with self.subTest(metric=metric_id):
                result = mod.load_fix_for_violation(metric_id)
                self.assertNotIn("No fix file", result, msg=f"Missing file for {metric_id}")
                self.assertGreater(len(result), 50)


class TestLoadFixInstructionsForFindings(unittest.TestCase):
    def _write(self, findings):
        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=".output.json", delete=False
        )
        json.dump({"findings": findings}, f)
        f.close()
        return f.name

    def test_single_finding_returns_content(self):
        path = self._write([{"metric_id": "OCP-1"}])
        result = mod.load_fix_instructions_for_findings(findings_path=path)
        self.assertIn("OCP-1", result)
        self.assertGreater(len(result), 50)

    def test_deduplicates_same_metric(self):
        path = self._write([{"metric_id": "OCP-1"}, {"metric_id": "OCP-1"}])
        result = mod.load_fix_instructions_for_findings(findings_path=path)
        self.assertEqual(result.count("OCP-1 Fix Strategy"), 1)

    def test_multiple_metrics_all_returned(self):
        path = self._write([{"metric_id": "OCP-1"}, {"metric_id": "LSP-3"}])
        result = mod.load_fix_instructions_for_findings(findings_path=path)
        self.assertIn("OCP-1", result)
        self.assertIn("LSP-3", result)

    def test_unknown_metric_noted_fail_open(self):
        path = self._write([{"metric_id": "OCP-1"}, {"metric_id": "OCP-99"}])
        result = mod.load_fix_instructions_for_findings(findings_path=path)
        self.assertIn("OCP-1", result)
        self.assertIn("fail-open", result.lower())

    def test_missing_file_returns_error_string(self):
        result = mod.load_fix_instructions_for_findings(
            findings_path="/tmp/does_not_exist_abc123.json"
        )
        self.assertIn("Could not read", result)

    def test_empty_findings_returns_message(self):
        path = self._write([])
        result = mod.load_fix_instructions_for_findings(findings_path=path)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_accepts_metric_field_alias(self):
        # Findings may use "metric" (review schema field) instead of "metric_id"
        path = self._write([{"metric": "SRP-2"}])
        result = mod.load_fix_instructions_for_findings(findings_path=path)
        self.assertIn("SRP-2", result)

    def test_principle_field_in_findings_ignored_gracefully(self):
        # Old findings format with explicit principle field still works
        path = self._write([{"principle": "OCP", "metric_id": "OCP-1"}])
        result = mod.load_fix_instructions_for_findings(findings_path=path)
        self.assertIn("OCP-1", result)

    def test_real_by_file_output_structure(self):
        # The actual by-file output uses "principles[].findings[].metric", not flat findings
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".output.json", delete=False)
        json.dump({
            "file_path": "/path/to/Foo.swift",
            "timestamp": "2026-01-01T00:00:00Z",
            "principles": [
                {
                    "principle": "Open/Closed Principle",
                    "agent": "ocp",
                    "severity": "SEVERE",
                    "findings": [
                        {"id": "ocp-001", "metric": "OCP-1", "severity": "SEVERE",
                         "title": "Sealed point", "issue": "..."},
                    ],
                    "suggestions": []
                },
                {
                    "principle": "Single Responsibility Principle",
                    "agent": "srp",
                    "severity": "SEVERE",
                    "findings": [
                        {"id": "srp-001", "metric": "SRP-2", "severity": "SEVERE",
                         "title": "Cohesion groups", "issue": "..."},
                    ],
                    "suggestions": []
                },
            ]
        }, f)
        f.close()
        result = mod.load_fix_instructions_for_findings(findings_path=f.name)
        self.assertIn("OCP-1", result)
        self.assertIn("SRP-2", result)


if __name__ == "__main__":
    unittest.main()
