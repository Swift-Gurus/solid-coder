"""Evaluates filtered collection counts deterministically."""

from dataclasses import replace

from harness.collection_metric_calculation import CollectionMetricCalculation
from harness.collection_metric_evaluating import CollectionMetricEvaluating
from harness.condition_decision_evaluating import ConditionDecisionEvaluating
from harness.resolved_workflow_context_value import ResolvedWorkflowContextValue
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: CollectionMetricEvaluator
solid-category: service
solid-spec: [SPEC-053]
solid-description: Calculates auditable metric values from authored collections and conditions.
"""
class CollectionMetricEvaluator(CollectionMetricEvaluating):
    def __init__(
        self,
        condition_evaluator: ConditionDecisionEvaluating,
    ) -> None:
        self._condition_evaluator = condition_evaluator

    def evaluate(
        self,
        calculation: CollectionMetricCalculation,
        entries: list[object],
        context: WorkflowRunContext,
    ) -> CollectionMetricCalculation:
        matched_indexes: list[int] = []
        excluded_indexes: list[int] = []
        condition_evidence = []
        for index, entry in enumerate(entries):
            condition = calculation.condition
            if condition is None:
                matched_indexes.append(index)
                continue
            evidence = self._condition_evaluator.evaluate(
                condition,
                replace(
                    context,
                    item=ResolvedWorkflowContextValue(
                        present=True,
                        value=entry,
                    ),
                ),
            )
            condition_evidence.append(evidence)
            target = matched_indexes if evidence.matched else excluded_indexes
            target.append(index)
        return CollectionMetricCalculation(
            source=calculation.source,
            condition=calculation.condition,
            value=len(matched_indexes),
            source_size=len(entries),
            matched_indexes=matched_indexes,
            excluded_indexes=excluded_indexes,
            condition_evidence=condition_evidence,
        )
