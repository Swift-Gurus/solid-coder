"""Defines negation of one workflow condition."""

from __future__ import annotations

from dataclasses import dataclass

from harness.composite_condition_evidence import CompositeConditionEvidence
from harness.condition_declaration import ConditionDeclaration
from harness.condition_runtime import ConditionRuntime
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: NotCondition
solid-category: model
solid-spec: [SPEC-037]
solid-description: Represents workflow eligibility that negates one nested criterion.
"""
@dataclass(frozen=True)
class NotCondition(ConditionDeclaration):
    condition: ConditionDeclaration

    def evaluate(
        self,
        runtime: ConditionRuntime,
        context: WorkflowRunContext,
    ) -> CompositeConditionEvidence:
        child = self.condition.evaluate(runtime, context)
        return CompositeConditionEvidence(
            kind="not",
            children=[child],
            matched=not child.matched,
        )
