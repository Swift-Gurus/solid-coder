"""
solid-description: Verifies that schema validation rejects invalid metrics and prevents their persistence.
solid-category: unit-test
"""

import unittest
from pathlib import Path
from tests.helpers import (
    SubmitFindingsTestBase,
    make_schema_srp_metrics,
    make_schema_srp_partial,
)


class TestSubmitFindingsValidation(SubmitFindingsTestBase):
    def test_valid_srp_metrics_passes_and_writes_file(self):
        result = self.handler.submit_findings(make_schema_srp_partial(), self.temp_path("out.json"))
        self.assertNotIn("error", result)
        self.assertTrue(Path(self.temp_path("out.json")).exists())

    def test_srp_missing_cohesion_groups_returns_error(self):
        bad = dict(make_schema_srp_metrics())
        del bad["cohesion_groups"]
        partial = make_schema_srp_partial([{"unit_name": "Foo", "unit_kind": "class", "metrics": bad}])
        result = self.handler.submit_findings(partial, self.temp_path("out.json"))
        self.assertIn("error", result)

    def test_srp_missing_cohesion_groups_writes_no_file(self):
        bad = dict(make_schema_srp_metrics())
        del bad["cohesion_groups"]
        partial = make_schema_srp_partial([{"unit_name": "Foo", "unit_kind": "class", "metrics": bad}])
        self.handler.submit_findings(partial, self.temp_path("out.json"))
        self.assertFalse(Path(self.temp_path("out.json")).exists())

    def test_srp_wrong_verb_count_type_returns_error(self):
        bad = make_schema_srp_metrics()
        bad["verbs"] = {"count": "two", "table": []}  # count must be integer
        partial = make_schema_srp_partial([{"unit_name": "Foo", "unit_kind": "class", "metrics": bad}])
        result = self.handler.submit_findings(partial, self.temp_path("out.json"))
        self.assertIn("error", result)

    def test_srp_wrong_verb_count_type_writes_no_file(self):
        bad = make_schema_srp_metrics()
        bad["verbs"] = {"count": "two", "table": []}
        partial = make_schema_srp_partial([{"unit_name": "Foo", "unit_kind": "class", "metrics": bad}])
        self.handler.submit_findings(partial, self.temp_path("out.json"))
        self.assertFalse(Path(self.temp_path("out.json")).exists())

    def test_scoring_absent_from_input_is_not_required(self):
        """Server fills scoring — LLM must not provide it, and absence must not fail validation."""
        partial = make_schema_srp_partial()
        self.assertNotIn("scoring", partial["files"][0]["units"][0])
        result = self.handler.submit_findings(partial, self.temp_path("out.json"))
        self.assertNotIn("error", result)

    def test_findings_absent_from_input_is_not_required(self):
        """Server fills findings — absence must not fail validation."""
        partial = make_schema_srp_partial()
        self.assertNotIn("findings", partial["files"][0]["units"][0])
        result = self.handler.submit_findings(partial, self.temp_path("out.json"))
        self.assertNotIn("error", result)

    def test_srp_empty_metrics_dict_returns_error(self):
        """Unit with metrics: {} fails for SRP because verbs/cohesion_groups/etc are required."""
        partial = make_schema_srp_partial([{"unit_name": "Foo", "unit_kind": "class", "metrics": {}}])
        result = self.handler.submit_findings(partial, self.temp_path("out.json"))
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()
