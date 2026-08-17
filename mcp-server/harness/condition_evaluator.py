"""Provides the workflow condition evaluation facade."""

from __future__ import annotations

from harness.comparison_condition import ComparisonCondition
from harness.comparison_condition_evidence import ComparisonConditionEvidence
from harness.condition_decision_evaluating import ConditionDecisionEvaluating
from harness.condition_declaration import ConditionDeclaration
from harness.condition_evidence import ConditionEvidence
from harness.condition_evaluating import ConditionEvaluating
from harness.condition_runtime import ConditionRuntime
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: ConditionEvaluator
solid-category: service
solid-spec: [SPEC-037]
solid-description: Delegates typed condition dispatch and runtime comparison.
"""
class ConditionEvaluator(ConditionDecisionEvaluating, ConditionRuntime):
    def __init__(
        self,
        declaration_evaluator: ConditionEvaluating,
        comparison_runtime: ConditionRuntime,
    ) -> None:
        self._declaration_evaluator = declaration_evaluator
        self._comparison_runtime = comparison_runtime

    def evaluate(
        self,
        condition: ConditionDeclaration,
        context: WorkflowRunContext,
    ) -> ConditionEvidence:
        return self._declaration_evaluator.evaluate(condition, self, context)

    def compare(
        self,
        condition: ComparisonCondition,
        context: WorkflowRunContext,
    ) -> ComparisonConditionEvidence:
        return self._comparison_runtime.compare(condition, context)
