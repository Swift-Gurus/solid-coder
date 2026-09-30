"""Composes reducer input decoding and metric compatibility checks."""

from pydantic import TypeAdapter

from harness.collection_metric_reducer_decoder import CollectionMetricReducerDecoder
from harness.collection_metric_reducer_decoding import CollectionMetricReducerDecoding
from harness.collection_metric_reducer_declaration import CollectionMetricReducerDeclaration
from harness.collection_metric_reducer_registration import CollectionMetricReducerRegistration
from harness.collection_metric_reducer_type import CollectionMetricReducerType
from harness.collection_metric_registration_selector import CollectionMetricRegistrationSelector
from harness.component_metric_reducer_declaration import ComponentMetricReducerDeclaration
from harness.component_metric_reducer_decoder import ComponentMetricReducerDecoder
from harness.condition_parsing import ConditionParsing
from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.metric_compatible_reducer_decoder import MetricCompatibleReducerDecoder
from harness.metric_reducer_value_compatibility import MetricReducerValueCompatibility
from harness.metric_value_type import MetricValueType
from harness.pairwise_relation_declaration import PairwiseRelationDeclaration
from harness.pairwise_relation_decoder import PairwiseRelationDecoder
from harness.projected_metric_reducer_declaration import ProjectedMetricReducerDeclaration
from harness.projected_metric_reducer_decoder import ProjectedMetricReducerDecoder
from harness.pydantic_model_decoder import PydanticModelDecoder
from harness.pydantic_type_adapter_decoder import PydanticTypeAdapterDecoder
from harness.ratio_metric_reducer_declaration import RatioMetricReducerDeclaration
from harness.ratio_metric_reducer_decoder import RatioMetricReducerDecoder
from harness.rooted_reference_path_decoder import RootedReferencePathDecoder
from harness.workflow_expression_parsing import WorkflowExpressionParsing


"""
solid-name: CollectionMetricReducerDecoderFactory
solid-category: factory
solid-spec: [SPEC-054, SPEC-059]
solid-description: Assembles supported collection metric decoders and their value compatibility policies.
"""
class CollectionMetricReducerDecoderFactory:
    def build(
        self,
        expression_parser: WorkflowExpressionParsing,
        condition_parser: ConditionParsing,
        error_factory: FlowValidationErrorCreating,
    ) -> CollectionMetricReducerDecoding:
        type_decoder = PydanticTypeAdapterDecoder(
            adapter=TypeAdapter(CollectionMetricReducerType)
        )
        projected = ProjectedMetricReducerDecoder(
            decoder=PydanticModelDecoder(model_type=ProjectedMetricReducerDeclaration),
            expression_parser=expression_parser,
            item_path_decoder=RootedReferencePathDecoder("item", expression_parser),
        )
        relation = PairwiseRelationDecoder(
            decoder=PydanticModelDecoder(model_type=PairwiseRelationDeclaration),
            expression_parser=expression_parser,
            left_path_decoder=RootedReferencePathDecoder("left", expression_parser),
            right_path_decoder=RootedReferencePathDecoder("right", expression_parser),
        )
        registrations = [
            CollectionMetricReducerRegistration(kind, projected)
            for kind in [
                CollectionMetricReducerType.MAXIMUM,
                CollectionMetricReducerType.MINIMUM,
                CollectionMetricReducerType.DISTINCT_COUNT,
            ]
        ]
        registrations.extend([
            CollectionMetricReducerRegistration(
                CollectionMetricReducerType.RATIO,
                RatioMetricReducerDecoder(
                    decoder=PydanticModelDecoder(model_type=RatioMetricReducerDeclaration),
                    condition_parser=condition_parser,
                ),
            ),
            CollectionMetricReducerRegistration(
                CollectionMetricReducerType.COMPONENT_COUNT,
                ComponentMetricReducerDecoder(
                    decoder=PydanticModelDecoder(model_type=ComponentMetricReducerDeclaration),
                    relation_decoder=relation,
                    reducer_type_decoder=type_decoder,
                ),
            ),
        ])
        integer = MetricReducerValueCompatibility(
            allowed_types=[MetricValueType.INTEGER],
            expected_description="an integer",
        )
        numeric = MetricReducerValueCompatibility(
            allowed_types=[MetricValueType.INTEGER, MetricValueType.NUMBER],
            expected_description="numeric",
        )
        number = MetricReducerValueCompatibility(
            allowed_types=[MetricValueType.NUMBER],
            expected_description="a number",
        )
        return MetricCompatibleReducerDecoder(
            delegate=CollectionMetricReducerDecoder(
                declaration_decoder=PydanticTypeAdapterDecoder(
                    adapter=TypeAdapter(CollectionMetricReducerDeclaration)
                ),
                selector=CollectionMetricRegistrationSelector(
                    registrations=registrations,
                    error_factory=error_factory,
                ),
                type_decoder=type_decoder,
            ),
            selector=CollectionMetricRegistrationSelector(
                registrations=[
                    CollectionMetricReducerRegistration(CollectionMetricReducerType.MAXIMUM, numeric),
                    CollectionMetricReducerRegistration(CollectionMetricReducerType.MINIMUM, numeric),
                    CollectionMetricReducerRegistration(CollectionMetricReducerType.DISTINCT_COUNT, integer),
                    CollectionMetricReducerRegistration(CollectionMetricReducerType.RATIO, number),
                    CollectionMetricReducerRegistration(CollectionMetricReducerType.COMPONENT_COUNT, integer),
                ],
                error_factory=error_factory,
            ),
            integer_compatibility=integer,
            error_factory=error_factory,
        )
