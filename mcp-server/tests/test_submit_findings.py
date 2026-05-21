"""
solid-description: Unit tests for submit_findings tool. Tests verify that a valid
SRP partial output writes a scored file and returns a summary, an empty files array
writes a clean-status document, and an unrecognised principle returns an error with
no file written.
solid-category: unit-test
"""

import json
import tempfile
import unittest
from pathlib import Path
from tests.helpers import make_handler, make_srp_partial, make_partial_output, make_standard_srp_partial


class TestSubmitFindings(unittest.TestCase):
    def setUp(self):
        self.handler = make_handler()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def _output_path(self, filename="out.json"):
        return str(Path(self.tmp.name) / filename)

    def _unknown_partial(self):
        return make_partial_output("nonexistent_xyz", "UNKNOWN", [
            {"path": "F.swift", "units": [{"name": "X", "kind": "class", "metrics": {}}]}
        ])

    def test_valid_partial_output_writes_output_file(self):
        self.handler.submit_findings(make_standard_srp_partial(), self._output_path())
        self.assertTrue(Path(self._output_path()).exists())

    def test_valid_partial_output_returns_summary_with_principle(self):
        result = self.handler.submit_findings(make_standard_srp_partial(), self._output_path("s1.json"))
        self.assertIn("principle", result)

    def test_valid_partial_output_returns_summary_with_unit_counts(self):
        result = self.handler.submit_findings(make_standard_srp_partial(), self._output_path("s2.json"))
        for key in ("total_units", "severe_count", "minor_count", "compliant_count"):
            self.assertIn(key, result)

    def test_empty_files_writes_file(self):
        path = self._output_path("clean.json")
        self.handler.submit_findings(make_srp_partial([]), path)
        self.assertTrue(Path(path).exists())

    def test_empty_files_writes_all_compliant_true(self):
        path = self._output_path("compliant.json")
        self.handler.submit_findings(make_srp_partial([]), path)
        doc = json.loads(Path(path).read_text())
        self.assertTrue(doc.get("all_compliant"))

    def test_empty_files_returns_zero_units(self):
        result = self.handler.submit_findings(make_srp_partial([]), self._output_path("zero.json"))
        self.assertEqual(result.get("total_units"), 0)

    def test_empty_files_returns_compliant_status(self):
        result = self.handler.submit_findings(make_srp_partial([]), self._output_path("status.json"))
        self.assertEqual(result.get("status"), "COMPLIANT")

    def test_unrecognised_principle_returns_error(self):
        result = self.handler.submit_findings(self._unknown_partial(), self._output_path("err.json"))
        self.assertIn("error", result)

    def test_unrecognised_principle_writes_no_file(self):
        path = self._output_path("no_file.json")
        self.handler.submit_findings(self._unknown_partial(), path)
        self.assertFalse(Path(path).exists())


if __name__ == "__main__":
    unittest.main()
