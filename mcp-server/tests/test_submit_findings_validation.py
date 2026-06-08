"""
solid-description: Verifies that findings submission rejects malformed metrics and prevents their persistence.
solid-category: unit-test
"""

import unittest
from pathlib import Path
from tests.helpers import (
    SubmitFindingsTestBase,
    make_schema_srp_metrics,
    make_schema_srp_partial,
    make_partial_output,
    make_unit,
    make_file,
)


class TestSubmitFindingsValidation(SubmitFindingsTestBase):
    def test_valid_srp_metrics_passes_and_writes_file(self):
        result = self.handler.submit_findings(make_schema_srp_partial(), self.temp_path("out.json"))
        self.assertNotIn("error", result)
        self.assertTrue(Path(self.temp_path("out.json")).exists())

    def test_srp_missing_cohesion_groups_returns_error(self):
        # Remove cohesion_groups from the SRP principle metrics sub-object
        metrics = {"SRP": {k: v for k, v in make_schema_srp_metrics()["SRP"].items() if k != "cohesion_groups"}}
        partial = make_partial_output([make_file("/tmp/Foo.swift", [make_unit("Foo", "class", metrics)])])
        result = self.handler.submit_findings(partial, self.temp_path("out.json"))
        self.assertIn("error", result)

    def test_srp_missing_cohesion_groups_writes_no_file(self):
        metrics = {"SRP": {k: v for k, v in make_schema_srp_metrics()["SRP"].items() if k != "cohesion_groups"}}
        partial = make_partial_output([make_file("/tmp/Foo.swift", [make_unit("Foo", "class", metrics)])])
        self.handler.submit_findings(partial, self.temp_path("out.json"))
        self.assertFalse(Path(self.temp_path("out.json")).exists())

    def test_srp_wrong_verb_count_type_returns_error(self):
        # value must be integer, not string
        bad_metrics = dict(make_schema_srp_metrics()["SRP"])
        bad_metrics["verb_count"] = {"value": "two"}
        partial = make_partial_output([make_file("/tmp/Foo.swift", [make_unit("Foo", "class", {"SRP": bad_metrics})])])
        result = self.handler.submit_findings(partial, self.temp_path("out.json"))
        self.assertIn("error", result)

    def test_srp_wrong_verb_count_type_writes_no_file(self):
        bad_metrics = dict(make_schema_srp_metrics()["SRP"])
        bad_metrics["verb_count"] = {"value": "two"}
        partial = make_partial_output([make_file("/tmp/Foo.swift", [make_unit("Foo", "class", {"SRP": bad_metrics})])])
        self.handler.submit_findings(partial, self.temp_path("out.json"))
        self.assertFalse(Path(self.temp_path("out.json")).exists())

    def test_violations_absent_from_input_is_not_required(self):
        """Server fills violations — absence must not fail validation."""
        partial = make_schema_srp_partial()
        self.assertNotIn("violations", partial["files"][0]["units"][0])
        result = self.handler.submit_findings(partial, self.temp_path("out.json"))
        self.assertNotIn("error", result)

    def test_srp_empty_principle_metrics_returns_error(self):
        """SRP key present but empty dict — misses required vars, schema validation fails."""
        metrics = {"SRP": {}}
        partial = make_partial_output([make_file("/tmp/Foo.swift", [make_unit("Foo", "class", metrics)])])
        result = self.handler.submit_findings(partial, self.temp_path("out.json"))
        self.assertIn("error", result)

    def test_empty_metrics_object_scores_compliant(self):
        """Unit with no principle keys scores compliant — no principles to evaluate."""
        metrics: dict = {}
        partial = make_partial_output([make_file("/tmp/Foo.swift", [make_unit("Foo", "class", metrics)])])
        result = self.handler.submit_findings(partial, self.temp_path("out.json"))
        self.assertNotIn("error", result)


if __name__ == "__main__":
    unittest.main()
