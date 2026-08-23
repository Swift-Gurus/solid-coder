"""Defines one locked rule result for the controlled review comparison."""

from pydantic import Field

from live_rule_validation_expectation import LiveRuleValidationExpectation


"""
solid-name: ReviewComparisonRuleExpectation
solid-category: test-support
solid-spec: [SPEC-036, SPEC-039, SPEC-041]
solid-description: Adds normalized source identity to the reusable live rule-result expectation for comparison accuracy checks.
"""
class ReviewComparisonRuleExpectation(LiveRuleValidationExpectation):
    source_index: int = Field(ge=0)
