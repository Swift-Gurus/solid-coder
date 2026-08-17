"""
solid-name: test_review_policy_parser
solid-category: unit-test
solid-spec: [SPEC-039]
solid-description: Verifies client review policy YAML decodes into a closed typed override hierarchy.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.flow_validation_error import FlowValidationError
from harness.flow_validation_error_factory import FlowValidationErrorFactory
from harness.pydantic_model_decoder import PydanticModelDecoder
from harness.review_policy import ReviewPolicy
from harness.review_policy_identity_validator import ReviewPolicyIdentityValidator
from harness.review_policy_parser import ReviewPolicyParser
from harness.scoring_band_severity import ScoringBandSeverity
from harness.scoring_comparison_operator import ScoringComparisonOperator
from harness.unique_string_validator import UniqueStringValidator


class TestReviewPolicyParser(unittest.TestCase):

    def setUp(self) -> None:
        error_factory = FlowValidationErrorFactory()
        self.sut = ReviewPolicyParser(
            decoder=PydanticModelDecoder(
                model_type=ReviewPolicy,
                error_factory=error_factory,
            ),
            validators=[
                ReviewPolicyIdentityValidator(
                    UniqueStringValidator(error_factory)
                )
            ],
        )

    def test_decodes_rule_metric_measurement_and_band_overrides(self):
        policy = self.sut.parse(
            {
                "version": 1,
                "rules": [
                    {
                        "workflow_id": "solid-srp-review",
                        "enabled": False,
                        "reason": "Temporarily disabled.",
                        "metrics": [
                            {
                                "id": "SRP-1",
                                "measurements": [
                                    {
                                        "name": "verb_count",
                                        "bands": [
                                            {
                                                "severity": "severe",
                                                "operator": "greater_than",
                                                "value": 8,
                                                "reason": "Larger units are accepted.",
                                            }
                                        ],
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        )

        rule = policy.rules[0]
        band = rule.metrics[0].measurements[0].bands[0]
        self.assertFalse(rule.enabled)
        self.assertEqual(band.severity, ScoringBandSeverity.SEVERE)
        self.assertEqual(band.operator, ScoringComparisonOperator.GREATER_THAN)
        self.assertEqual(band.value, 8)

    def test_omitted_enablement_is_preserved_as_no_client_request(self):
        policy = self.sut.parse(
            {"version": 1, "rules": [{"workflow_id": "solid-srp-review"}]}
        )

        self.assertIsNone(policy.rules[0].enabled)

    def test_unknown_fields_are_rejected(self):
        with self.assertRaisesRegex(FlowValidationError, "Invalid review policy"):
            self.sut.parse({"version": 1, "rules": [], "automatic": True})

    def test_duplicate_rule_records_are_rejected(self):
        with self.assertRaisesRegex(
            FlowValidationError,
            "Duplicate review policy workflow_id",
        ):
            self.sut.parse(
                {
                    "version": 1,
                    "rules": [
                        {"workflow_id": "same-rule"},
                        {"workflow_id": "same-rule"},
                    ],
                }
            )

    def test_duplicate_metric_records_are_rejected_within_their_rule(self):
        with self.assertRaisesRegex(
            FlowValidationError,
            "Duplicate review policy metric ID",
        ):
            self.sut.parse(
                {
                    "version": 1,
                    "rules": [
                        {
                            "workflow_id": "solid-srp-review",
                            "metrics": [{"id": "SRP-1"}, {"id": "SRP-1"}],
                        }
                    ],
                }
            )


if __name__ == "__main__":
    unittest.main()
