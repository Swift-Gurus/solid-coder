"""Defines conjunction of workflow conditions."""

from __future__ import annotations

from dataclasses import dataclass

from harness.composite_condition_evidence import CompositeConditionEvidence
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
    ) -> CompositeConditionEvidence:
        children = []
        for condition in self.conditions:
            evidence = condition.evaluate(runtime, context)
            children.append(evidence)
            if not evidence.matched:
                return CompositeConditionEvidence(
                    kind="all",
                    children=children,
                    matched=False,
                )
        return CompositeConditionEvidence(
            kind="all",
            children=children,
            matched=True,
        )
