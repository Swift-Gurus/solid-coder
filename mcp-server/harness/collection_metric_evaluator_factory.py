"""Assembles deterministic collection metric evaluation."""

from harness.collection_metric_evaluating import CollectionMetricEvaluating
from harness.collection_metric_evaluator import CollectionMetricEvaluator
from harness.collection_metric_projection_resolver import (
    CollectionMetricProjectionResolver,
)
from harness.collection_metric_reducer_registration import (
    CollectionMetricReducerRegistration,
)
from harness.collection_metric_reducer_selector import (
    CollectionMetricReducerSelector,
)
from harness.collection_metric_reducer_type import CollectionMetricReducerType
from harness.condition_decision_evaluating import ConditionDecisionEvaluating
from harness.distinct_count_collection_metric_reducer import (
    DistinctCountCollectionMetricReducer,
)
from harness.expression_evaluating import ExpressionEvaluating
from harness.extreme_collection_metric_reducer import (
    ExtremeCollectionMetricReducer,
)
from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.maximum_collection_metric_value_selector import (
    MaximumCollectionMetricValueSelector,
)
from harness.minimum_collection_metric_value_selector import (
    MinimumCollectionMetricValueSelector,
)
from harness.ratio_collection_metric_reducer import RatioCollectionMetricReducer
from harness.strict_value_comparing import StrictValueComparing
from harness.workflow_step_context_resolving import WorkflowStepContextResolving


"""
solid-name: CollectionMetricEvaluatorFactory
solid-category: service
solid-spec: [SPEC-054]
solid-description: Enables workflows to derive auditable metric values from filtered observation collections without model arithmetic.
"""
class CollectionMetricEvaluatorFactory:
    def build(
        self,
        condition_evaluator: ConditionDecisionEvaluating,
        expression_evaluator: ExpressionEvaluating,
        value_comparator: StrictValueComparing,
        context_resolver: WorkflowStepContextResolving,
        error_factory: FlowValidationErrorCreating,
    ) -> CollectionMetricEvaluating:
        projection_resolver = CollectionMetricProjectionResolver(
            expression_evaluator=expression_evaluator,
            error_factory=error_factory,
        )
        maximum = ExtremeCollectionMetricReducer(
            projection_resolver=projection_resolver,
            value_selector=MaximumCollectionMetricValueSelector(),
            reducer_name="maximum",
            error_factory=error_factory,
        )
        minimum = ExtremeCollectionMetricReducer(
            projection_resolver=projection_resolver,
            value_selector=MinimumCollectionMetricValueSelector(),
            reducer_name="minimum",
            error_factory=error_factory,
        )
        return CollectionMetricEvaluator(
            condition_evaluator=condition_evaluator,
            reducer=CollectionMetricReducerSelector(
                registrations=[
                    CollectionMetricReducerRegistration(
                        CollectionMetricReducerType.MAXIMUM,
                        maximum,
                    ),
                    CollectionMetricReducerRegistration(
                        CollectionMetricReducerType.MINIMUM,
                        minimum,
                    ),
                    CollectionMetricReducerRegistration(
                        CollectionMetricReducerType.DISTINCT_COUNT,
                        DistinctCountCollectionMetricReducer(
                            projection_resolver=projection_resolver,
                            value_comparator=value_comparator,
                        ),
                    ),
                    CollectionMetricReducerRegistration(
                        CollectionMetricReducerType.RATIO,
                        RatioCollectionMetricReducer(
                            condition_evaluator=condition_evaluator,
                            error_factory=error_factory,
                        ),
                    ),
                ],
                error_factory=error_factory,
            ),
            context_resolver=context_resolver,
        )
