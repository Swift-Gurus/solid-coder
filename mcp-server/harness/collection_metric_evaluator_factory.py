"""Assembles deterministic collection metric evaluation."""

from typing import Optional

from pydantic import TypeAdapter

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
from harness.collection_metric_registration_selector import CollectionMetricRegistrationSelector
from harness.component_metrics.component_count_metric_reducer import ComponentCountMetricReducer
from harness.component_metrics.connected_index_groups import ConnectedIndexGroups
from harness.component_metrics.intersecting_pair_resolver import IntersectingPairResolver
from harness.component_metrics.pairwise_metric_projection_resolver import PairwiseMetricProjectionResolver
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
from harness.ratio_value_calculator import RatioValueCalculator
from harness.metric_scoring_band import MetricComparisonValue
from harness.nested_value_resolving import NestedValueResolving
from harness.pydantic_type_adapter_decoder import PydanticTypeAdapterDecoder
from harness.strict_collection_value_matcher import StrictCollectionValueMatcher
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
        nested_value_resolver: NestedValueResolving,
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
        components = ComponentCountMetricReducer(
            projection_resolver=PairwiseMetricProjectionResolver(
                path_resolver=nested_value_resolver,
                array_decoder=PydanticTypeAdapterDecoder(
                    adapter=TypeAdapter(list[Optional[MetricComparisonValue]]),
                ),
                error_factory=error_factory,
            ),
            edge_resolver=IntersectingPairResolver(
                matcher=StrictCollectionValueMatcher(value_comparator),
            ),
            component_resolver=ConnectedIndexGroups(),
        )
        registrations = [
            CollectionMetricReducerRegistration(CollectionMetricReducerType.MAXIMUM, maximum),
            CollectionMetricReducerRegistration(CollectionMetricReducerType.MINIMUM, minimum),
            CollectionMetricReducerRegistration(CollectionMetricReducerType.COMPONENT_COUNT, components),
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
                    value_calculator=RatioValueCalculator(),
                    error_factory=error_factory,
                ),
            ),
        ]
        return CollectionMetricEvaluator(
            condition_evaluator=condition_evaluator,
            reducer=CollectionMetricReducerSelector(
                selector=CollectionMetricRegistrationSelector(
                    registrations=registrations,
                    error_factory=error_factory,
                ),
            ),
            context_resolver=context_resolver,
        )
