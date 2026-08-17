"""Defines runtime workflow condition decisions."""

from __future__ import annotations

from typing import Protocol

from harness.condition_declaration import ConditionDeclaration
from harness.condition_evidence import ConditionEvidence
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: ConditionDecisionEvaluating
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for evaluating one typed condition against runtime context.
"""
class ConditionDecisionEvaluating(Protocol):
    def evaluate(
        self,
        condition: ConditionDeclaration,
        context: WorkflowRunContext,
    ) -> ConditionEvidence: ...
