"""Defines one prerequisite rule-analysis output used by workflow tests."""

from pydantic import BaseModel, ConfigDict, Field


"""
solid-name: RuleAnalysisExpectation
solid-category: test-support
solid-spec: [SPEC-039]
solid-description: Carries one prerequisite rule-analysis step identity and its model-facing test output.
"""
class RuleAnalysisExpectation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    step_id: str = Field(min_length=1)
    output: dict[str, object]
