"""Dispatches typed workflow condition declarations."""

from __future__ import annotations

from harness.condition_declaration import ConditionDeclaration
from harness.condition_evidence import ConditionEvidence
from harness.condition_evaluating import ConditionEvaluating
from harness.condition_runtime import ConditionRuntime
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: ConditionDeclarationEvaluator
solid-category: service
solid-spec: [SPEC-037]
solid-description: Dispatches a typed condition declaration through its supplied runtime.
"""
class ConditionDeclarationEvaluator(ConditionEvaluating):
    def evaluate(
        self,
        condition: ConditionDeclaration,
        runtime: ConditionRuntime,
        context: WorkflowRunContext,
    ) -> ConditionEvidence:
        return condition.evaluate(runtime, context)
