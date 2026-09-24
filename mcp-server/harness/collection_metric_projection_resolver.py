"""Resolves scalar projections for collection metric reducers."""

from harness.collection_metric_projection_evidence import (
    CollectionMetricProjectionEvidence,
)
from harness.collection_metric_projection_resolving import (
    CollectionMetricProjectionResolving,
)
from harness.collection_metric_reducer import CollectionMetricReducer
from harness.expression_evaluating import ExpressionEvaluating
from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.selected_collection_metric_entry import SelectedCollectionMetricEntry


"""
solid-name: CollectionMetricProjectionResolver
solid-category: service
solid-spec: [SPEC-054]
solid-description: Resolves schema-validated observation fields into auditable reducer inputs.
"""
class CollectionMetricProjectionResolver(CollectionMetricProjectionResolving):
    def __init__(
        self,
        expression_evaluator: ExpressionEvaluating,
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._expression_evaluator = expression_evaluator
        self._error_factory = error_factory

    def resolve(
        self,
        declaration: CollectionMetricReducer,
        entries: list[SelectedCollectionMetricEntry],
    ) -> list[CollectionMetricProjectionEvidence]:
        reference = declaration.value
        if reference is None:
            raise self._error_factory.create("Metric reducer requires a value reference")
        return [
            CollectionMetricProjectionEvidence(
                index=entry.source_index,
                value=self._expression_evaluator.evaluate(
                    reference.value,
                    entry.context,
                ),
            )
            for entry in entries
        ]
