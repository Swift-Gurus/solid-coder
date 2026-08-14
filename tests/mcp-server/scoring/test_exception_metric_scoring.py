"""Verifies server scoring policy for submitted metric exceptions."""

from helpers import (
    SubmitFindingsTestBase,
    make_schema_srp_partial,
    make_schema_srp_severe_metrics,
)


"""
solid-name: ExceptionMetricScoringTests
solid-category: unit-test
solid-description: Verifies that explicitly classified metric exceptions do not produce violations.
"""
class ExceptionMetricScoringTests(SubmitFindingsTestBase):
    def test_exception_measurements_are_scored_compliant(self):
        metrics = make_schema_srp_severe_metrics()
        for measurement in metrics["SRP"].values():
            measurement["is_exception"] = True
            measurement["additional_info"]["reasoning"] = (
                "The reviewed unit satisfies a documented SRP exception."
            )
        partial = make_schema_srp_partial(units=[{
            "unit_name": "GeneratedAdapter",
            "unit_kind": "class",
            "metrics": metrics,
        }])

        result = self.handler.submit_batch_findings(
            self.tmp.name,
            {"SRP": partial},
        )

        self.assertEqual(result.get("violations"), [])
