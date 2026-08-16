"""Defines disjunction of workflow conditions."""

from __future__ import annotations

from dataclasses import dataclass

from harness.condition_declaration import ConditionDeclaration
from harness.condition_runtime import ConditionRuntime
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: AnyCondition
solid-category: model
solid-spec: [SPEC-037]
solid-description: Represents workflow eligibility satisfied by any nested criterion.
"""
@dataclass(frozen=True)
class AnyCondition(ConditionDeclaration):
    conditions: tuple[ConditionDeclaration, ...]

    def evaluate(
        self,
        runtime: ConditionRuntime,
        context: WorkflowRunContext,
    ) -> bool:
        return any(condition.evaluate(runtime, context) for condition in self.conditions)
