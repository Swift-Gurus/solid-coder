"""Defines audit evidence for one workflow condition comparison."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

from harness.condition_operator import ConditionOperator
from harness.resolved_condition_value import ResolvedConditionValue


"""
solid-name: ComparisonConditionEvidence
solid-category: model
solid-spec: [SPEC-037]
solid-description: Captures the operands and outcome of one workflow condition comparison.
"""
class ComparisonConditionEvidence(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: Literal["comparison"] = "comparison"
    reference: str
    operator: ConditionOperator
    expected: object
    actual: ResolvedConditionValue
    matched: bool
