"""Defines conjunction of workflow conditions."""

from __future__ import annotations

from dataclasses import dataclass

from harness.condition_declaration import ConditionDeclaration
from harness.condition_runtime import ConditionRuntime
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: AllCondition
solid-category: model
solid-spec: [SPEC-037]
solid-description: Represents workflow eligibility that requires every nested criterion.
"""
@dataclass(frozen=True)
class AllCondition(ConditionDeclaration):
    conditions: tuple[ConditionDeclaration, ...]

    def evaluate(
        self,
        runtime: ConditionRuntime,
        context: WorkflowRunContext,
    ) -> bool:
        return all(condition.evaluate(runtime, context) for condition in self.conditions)
