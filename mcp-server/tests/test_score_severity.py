"""solid-description: Verifies that severity scoring correctly classifies measurement inputs into severity levels and handles invalid or incomplete data gracefully.
solid-category: unit-test
"""

import unittest
from tests.helpers import (
    SubmitFindingsTestBase,
    make_partial_output,
    make_srp_file,
    make_schema_srp_metrics,
    make_schema_srp_severe_metrics,
)


class TestScoreSeverity(SubmitFindingsTestBase):
    def _score_first_unit(self, metrics: dict) -> dict:
        output = make_partial_output([make_srp_file(metrics)])
        result = self.handler.score_severity([output])
        return result["results"][0]["files"][0]["units"][0]

    def _severities(self, unit: dict) -> set:
        return {v["severity"] for v in unit.get("violations", [])}

    def test_srp_cohesion_groups_2_yields_severe(self):
        """Complete SRP metrics with 2 cohesion groups → SRP-2 SEVERE."""
        unit = self._score_first_unit(make_schema_srp_severe_metrics())
        self.assertIn("SEVERE", self._severities(unit))

    def test_srp_verb_count_2_cohesion_groups_1_yields_compliant(self):
        """Complete SRP metrics with 2 verbs and 1 cohesion group → all COMPLIANT."""
        unit = self._score_first_unit(make_schema_srp_metrics())
        self.assertEqual(unit.get("violations", []), [])

    def test_complete_metrics_with_no_violations_returns_no_error(self):
        """Providing complete, well-formed metrics must not produce an error entry."""
        output = make_partial_output([make_srp_file(make_schema_srp_metrics())])
        result = self.handler.score_severity([output])
        self.assertNotIn("error", result["results"][0])

    def test_unknown_principle_key_returns_error(self):
        """Metrics with an unrecognised principle key returns an error — fail-fast."""
        output = make_partial_output([make_srp_file({"UNKNOWN": {"foo": {"value": 1}}})])
        result = self.handler.score_severity([output])
        self.assertIn("error", result["results"][0])

    def test_two_entries_both_scored(self):
        srp_output = make_partial_output([make_srp_file(make_schema_srp_metrics())])
        empty_output = make_partial_output([])
        result = self.handler.score_severity([srp_output, empty_output])
        self.assertEqual(len(result["results"]), 2)

    def test_scored_unit_has_violations_field(self):
        """Scoring result must include a violations field."""
        unit = self._score_first_unit(make_schema_srp_severe_metrics())
        self.assertIn("violations", unit)
        self.assertIsInstance(unit["violations"], list)

    def test_violations_have_rule_id_and_severity(self):
        """Each violation must have rule_id and severity."""
        unit = self._score_first_unit(make_schema_srp_severe_metrics())
        for v in unit["violations"]:
            self.assertIn("rule_id", v)
            self.assertIn("severity", v)


if __name__ == "__main__":
    unittest.main()
