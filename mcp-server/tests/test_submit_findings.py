"""solid-description: Verifies findings submission processes analysis findings and produces structured compliance summaries.
solid-category: unit-test
"""

import json
import unittest
from pathlib import Path
from tests.helpers import (
    SubmitFindingsTestBase,
    make_partial_output,
    make_standard_srp_partial,
    make_file,
    make_unit,
)


class TestSubmitFindings(SubmitFindingsTestBase):
    def _output_path(self, filename="out.json"):
        return self.temp_path(filename)

    def _unknown_partial(self):
        # Unit with an unrecognised principle key — scorer lookup will fail
        metrics = {"NONEXISTENT_XYZ": {"some_metric": {"value": 0}}}
        return make_partial_output([
            make_file("F.swift", [make_unit("X", "class", metrics)])
        ])

    def test_valid_partial_output_writes_output_file(self):
        self.handler.submit_findings(make_standard_srp_partial(), self._output_path())
        self.assertTrue(Path(self._output_path()).exists())

    def test_valid_partial_output_returns_unit_counts(self):
        result = self.handler.submit_findings(make_standard_srp_partial(), self._output_path("s1.json"))
        for key in ("total_units", "severe_count", "minor_count", "compliant_count"):
            self.assertIn(key, result)

    def test_valid_partial_output_returns_status(self):
        result = self.handler.submit_findings(make_standard_srp_partial(), self._output_path("s2.json"))
        self.assertIn("status", result)

    def test_empty_files_writes_file(self):
        path = self._output_path("clean.json")
        self.handler.submit_findings(make_partial_output([]), path)
        self.assertTrue(Path(path).exists())

    def test_empty_files_writes_empty_files_list(self):
        path = self._output_path("compliant.json")
        self.handler.submit_findings(make_partial_output([]), path)
        doc = json.loads(Path(path).read_text())
        self.assertEqual(doc.get("files"), [])

    def test_empty_files_returns_zero_units(self):
        result = self.handler.submit_findings(make_partial_output([]), self._output_path("zero.json"))
        self.assertEqual(result.get("total_units"), 0)

    def test_empty_files_returns_compliant_status(self):
        result = self.handler.submit_findings(make_partial_output([]), self._output_path("status.json"))
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
