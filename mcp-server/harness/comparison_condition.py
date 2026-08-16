"""Defines one workflow condition comparison."""

from __future__ import annotations

from dataclasses import dataclass

from harness.condition_declaration import ConditionDeclaration
from harness.condition_operator import ConditionOperator
from harness.condition_runtime import ConditionRuntime
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: ComparisonCondition
solid-category: model
solid-spec: [SPEC-037]
solid-description: Represents one type-strict workflow eligibility criterion.
"""
@dataclass(frozen=True)
class ComparisonCondition(ConditionDeclaration):
    reference: str
    operator: ConditionOperator
    expected: object

    def evaluate(
        self,
        runtime: ConditionRuntime,
        context: WorkflowRunContext,
    ) -> bool:
        return runtime.compare(self, context)
