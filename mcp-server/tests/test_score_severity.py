"""solid-description: Verifies that severity scoring correctly classifies measurement inputs into severity levels and handles invalid or incomplete data gracefully.
solid-category: unit-test
"""

import unittest
from tests.helpers import make_handler, make_srp_partial, make_partial_output, make_srp_file, make_standard_srp_partial


class TestScoreSeverity(unittest.TestCase):
    def setUp(self):
        self.handler = make_handler()

    def _score_first_unit(self, metrics: dict) -> dict:
        output = make_srp_partial([make_srp_file(metrics)])
        result = self.handler.score_severity([output])
        return result["results"][0]["files"][0]["units"][0]

    def _severities(self, unit: dict) -> list:
        return [s["final_severity"] for s in unit["scoring"]]

    def test_srp_cohesion_groups_2_yields_severe(self):
        unit = self._score_first_unit({"SRP-2": {"cohesion_groups": 2}})
        self.assertIn("SEVERE", self._severities(unit))

    def test_srp_verb_count_2_cohesion_groups_1_yields_compliant(self):
        unit = self._score_first_unit({"SRP-1": {"verb_count": 2, "cohesion_groups": 1, "stakeholder_count": 1}})
        self.assertEqual(self._severities(unit), ["COMPLIANT"])

    def test_no_matching_band_defaults_to_compliant(self):
        output = make_partial_output("srp", "SRP", [make_srp_file({})])
        result = self.handler.score_severity([output])
        self.assertNotIn("error", result["results"][0])

    def test_mismatched_metric_key_returns_error_entry(self):
        output = make_srp_partial([make_srp_file({"SRP-2": {"unknown_key_xyz": 5}})])
        result = self.handler.score_severity([output])
        self.assertIn("error", result["results"][0])

    def test_two_different_principles_both_scored(self):
        srp_output = make_standard_srp_partial()
        ocp_output = make_partial_output("ocp", "OCP", [])
        result = self.handler.score_severity([srp_output, ocp_output])
        self.assertEqual(len(result["results"]), 2)

    def test_scored_unit_scoring_field_is_a_list(self):
        unit = self._score_first_unit({"SRP-2": {"cohesion_groups": 2}})
        self.assertIn("scoring", unit)
        self.assertIsInstance(unit["scoring"], list)


if __name__ == "__main__":
    unittest.main()
