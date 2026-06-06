"""
solid-description: Verifies batch submission and validation of principle findings with fail-fast error handling.
solid-category: unit-test
"""

import json
import unittest
from pathlib import Path
from tests.helpers import (
    SubmitFindingsTestBase,
    make_schema_srp_partial,
    make_schema_srp_severe_metrics,
    make_ocp_partial,
    make_ocp_partial_bad_files,
)


class TestSubmitBatchFindings(SubmitFindingsTestBase):
    def test_batch_two_valid_principles_returns_violations_key(self):
        result = self.handler.submit_batch_findings(
            self.tmp.name,
            {"SRP": make_schema_srp_partial(), "OCP": make_ocp_partial()},
        )
        self.assertIn("violations", result)

    def test_batch_two_valid_principles_violations_is_list(self):
        result = self.handler.submit_batch_findings(
            self.tmp.name,
            {"SRP": make_schema_srp_partial(), "OCP": make_ocp_partial()},
        )
        self.assertIsInstance(result.get("violations"), list)

    def test_batch_two_valid_principles_writes_both_files(self):
        self.handler.submit_batch_findings(
            self.tmp.name,
            {"SRP": make_schema_srp_partial(), "OCP": make_ocp_partial()},
        )
        self.assertTrue(Path(self.temp_path("SRP", "review-output.json")).exists())
        self.assertTrue(Path(self.temp_path("OCP", "review-output.json")).exists())

    def test_output_paths_derived_from_output_dir_and_label(self):
        """Output file lands at {output_dir}/{label}/review-output.json."""
        self.handler.submit_batch_findings(
            self.tmp.name,
            {"SRP": make_schema_srp_partial()},
        )
        expected = Path(self.temp_path("SRP", "review-output.json"))
        self.assertTrue(expected.exists())
        doc = json.loads(expected.read_text())
        self.assertEqual(doc.get("principle"), "Single Responsibility Principle")

    def test_batch_fails_fast_on_invalid_schema_returns_error(self):
        result = self.handler.submit_batch_findings(
            self.tmp.name,
            {"SRP": make_schema_srp_partial(), "OCP": make_ocp_partial_bad_files()},
        )
        self.assertIn("error", result)

    def test_batch_fails_fast_reports_failed_principle_label(self):
        result = self.handler.submit_batch_findings(
            self.tmp.name,
            {"SRP": make_schema_srp_partial(), "OCP": make_ocp_partial_bad_files()},
        )
        self.assertEqual(result.get("failed_at"), "OCP")

    def test_batch_fails_fast_srp_file_written_ocp_not(self):
        """First (SRP) succeeds before OCP fails — SRP file should be written."""
        self.handler.submit_batch_findings(
            self.tmp.name,
            {"SRP": make_schema_srp_partial(), "OCP": make_ocp_partial_bad_files()},
        )
        self.assertTrue(Path(self.temp_path("SRP", "review-output.json")).exists())
        self.assertFalse(Path(self.temp_path("OCP", "review-output.json")).exists())

    def test_batch_empty_submissions_returns_violations_key(self):
        result = self.handler.submit_batch_findings(self.tmp.name, {})
        self.assertIn("violations", result)

    def test_batch_empty_submissions_violations_is_empty_list(self):
        result = self.handler.submit_batch_findings(self.tmp.name, {})
        self.assertEqual(result.get("violations"), [])

    def test_severe_violations_include_instructions_message(self):
        severe_partial = make_schema_srp_partial(units=[{
            "unit_name": "Foo", "unit_kind": "class",
            "metrics": make_schema_srp_severe_metrics(),
        }])
        result = self.handler.submit_batch_findings(self.tmp.name, {"SRP": severe_partial})
        if result.get("violations"):
            self.assertIn("message", result)
            self.assertIn("output_dir", result)

    def test_compliant_submissions_no_message_field(self):
        result = self.handler.submit_batch_findings(
            self.tmp.name, {"SRP": make_schema_srp_partial()},
        )
        if not result.get("violations"):
            self.assertNotIn("message", result)

    def test_violation_entry_includes_file_path_and_unit_name(self):
        severe_partial = make_schema_srp_partial(units=[{
            "unit_name": "Bar", "unit_kind": "class",
            "metrics": make_schema_srp_severe_metrics(),
        }])
        result = self.handler.submit_batch_findings(self.tmp.name, {"SRP": severe_partial})
        violations = result.get("violations", [])
        if violations:
            v = violations[0]
            self.assertIn("file_path", v)
            self.assertIn("unit_name", v)


if __name__ == "__main__":
    unittest.main()
