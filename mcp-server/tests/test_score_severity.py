"""solid-description: Verifies that severity scoring correctly classifies measurement inputs into severity levels and handles invalid or incomplete data gracefully.
solid-category: unit-test
"""

import unittest
from tests.helpers import (
    SubmitFindingsTestBase,
    make_srp_partial,
    make_partial_output,
    make_srp_file,
    make_schema_srp_metrics,
    make_schema_srp_severe_metrics,
)


class TestScoreSeverity(SubmitFindingsTestBase):
    def _score_first_unit(self, metrics: dict) -> dict:
        output = make_srp_partial([make_srp_file(metrics)])
        result = self.handler.score_severity([output])
        return result["results"][0]["files"][0]["units"][0]

    def _severities(self, unit: dict) -> list:
        return [s["final_severity"] for s in unit["scoring"]]

    def test_srp_cohesion_groups_2_yields_severe(self):
        """Complete SRP metrics with 2 cohesion groups → SRP-2 SEVERE."""
        unit = self._score_first_unit(make_schema_srp_severe_metrics())
        self.assertIn("SEVERE", self._severities(unit))

    def test_srp_verb_count_2_cohesion_groups_1_yields_compliant(self):
        """Complete SRP metrics with 2 verbs and 1 cohesion group → SRP-1 COMPLIANT."""
        unit = self._score_first_unit(make_schema_srp_metrics())
        self.assertIn("COMPLIANT", self._severities(unit))

    def test_complete_metrics_with_no_violations_returns_no_error(self):
        """Providing complete, well-formed metrics must not produce an error entry."""
        output = make_srp_partial([make_srp_file(make_schema_srp_metrics())])
        result = self.handler.score_severity([output])
        self.assertNotIn("error", result["results"][0])

    def test_incomplete_metrics_returns_error_entry(self):
        """Providing incomplete metrics (old metric_id-keyed format) triggers an error.

        The LLM must provide the complete semantic metric set. Partial or wrongly-keyed
        metrics cause a NameError when evaluating severity-band conditions, which the
        server propagates as an error to enforce correct LLM output.
        """
        output = make_srp_partial([make_srp_file({"SRP-2": {"cohesion_groups": 2}})])
        result = self.handler.score_severity([output])
        self.assertIn("error", result["results"][0])

    def test_two_different_principles_both_scored(self):
        srp_output = make_srp_partial([make_srp_file(make_schema_srp_metrics())])
        ocp_output = make_partial_output("ocp", "OCP", [])
        result = self.handler.score_severity([srp_output, ocp_output])
        self.assertEqual(len(result["results"]), 2)

    def test_scored_unit_scoring_field_is_a_list(self):
        """Scoring result must include a list-typed scoring field."""
        unit = self._score_first_unit(make_schema_srp_severe_metrics())
        self.assertIn("scoring", unit)
        self.assertIsInstance(unit["scoring"], list)


if __name__ == "__main__":
    unittest.main()
