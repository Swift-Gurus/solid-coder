"""Evaluates filtered collection metrics deterministically."""

from harness.collection_metric_calculation import CollectionMetricCalculation
from harness.collection_metric_evaluating import CollectionMetricEvaluating
from harness.collection_metric_reducing import CollectionMetricReducing
from harness.condition_decision_evaluating import ConditionDecisionEvaluating
from harness.selected_collection_metric_entry import SelectedCollectionMetricEntry
from harness.workflow_run_context import WorkflowRunContext
from harness.workflow_step_context_resolving import WorkflowStepContextResolving


"""
solid-name: CollectionMetricEvaluator
solid-category: service
solid-spec: [SPEC-053, SPEC-054]
solid-description: Produces deterministic, auditable metric values from schema-validated observation collections.
"""
class CollectionMetricEvaluator(CollectionMetricEvaluating):
    def __init__(
        self,
        condition_evaluator: ConditionDecisionEvaluating,
        reducer: CollectionMetricReducing,
        context_resolver: WorkflowStepContextResolving,
    ) -> None:
        self._condition_evaluator = condition_evaluator
        self._reducer = reducer
        self._context_resolver = context_resolver

    def evaluate(
        self,
        calculation: CollectionMetricCalculation,
        entries: list[object],
        context: WorkflowRunContext,
    ) -> CollectionMetricCalculation:
        matched_indexes: list[int] = []
        selected_entries: list[SelectedCollectionMetricEntry] = []
        excluded_indexes: list[int] = []
        condition_evidence = []
        for index, entry in enumerate(entries):
            item_context = self._context_resolver.resolve_item(context, entry)
            condition = calculation.condition
            if condition is None:
                matched_indexes.append(index)
                selected_entries.append(
                    SelectedCollectionMetricEntry(
                        source_index=index,
                        value=entry,
                        context=item_context,
                    )
                )
                continue
            evidence = self._condition_evaluator.evaluate(
                condition,
                item_context,
            )
            condition_evidence.append(evidence)
            target = matched_indexes if evidence.matched else excluded_indexes
            target.append(index)
            if evidence.matched:
                selected_entries.append(
                    SelectedCollectionMetricEntry(
                        source_index=index,
                        value=entry,
                        context=item_context,
                    )
                )
        reducer = calculation.reducer
        if reducer is None:
            value = len(matched_indexes)
            reduction = None
        else:
            reduction = self._reducer.reduce(reducer, selected_entries)
            value = reduction.value
        return CollectionMetricCalculation(
            source=calculation.source,
            condition=calculation.condition,
            reducer=reducer,
            value=value,
            source_size=len(entries),
            matched_indexes=matched_indexes,
            excluded_indexes=excluded_indexes,
            condition_evidence=condition_evidence,
            projection_evidence=(
                reduction.projection_evidence if reduction is not None else []
            ),
            distinct_indexes=(
                reduction.distinct_indexes if reduction is not None else []
            ),
            numerator_indexes=(
                reduction.numerator_indexes if reduction is not None else []
            ),
            denominator_indexes=(
                reduction.denominator_indexes if reduction is not None else []
            ),
            numerator_condition_evidence=(
                reduction.numerator_condition_evidence
                if reduction is not None
                else []
            ),
            denominator_condition_evidence=(
                reduction.denominator_condition_evidence
                if reduction is not None
                else []
            ),
            zero_denominator=(
                reduction.zero_denominator if reduction is not None else False
            ),
        )
