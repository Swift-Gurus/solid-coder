"""Decodes workflow metric fields into a typed declaration."""

from harness.collection_metric_reducer_decoding import (
    CollectionMetricReducerDecoding,
)
from harness.collection_source_reference_parsing import (
    CollectionSourceReferenceParsing,
)
from harness.condition_parsing import ConditionParsing
from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.metric_declaration import MetricDeclaration
from harness.metric_declaration_decoding import MetricDeclarationDecoding
from harness.metric_step_contract import MetricStepContract
from harness.metric_step_contract_assembling import MetricStepContractAssembling
from harness.metric_value_type import MetricValueType
from harness.structured_model_decoding import StructuredModelDecoding
from harness.workflow_expression_parsing import WorkflowExpressionParsing

"""
solid-name: MetricDeclarationDecoder
solid-category: boundary-adapter
solid-spec: [SPEC-039, SPEC-054, SPEC-056]
solid-description: Produces validated executable measurement contracts from authored configuration.
"""


class MetricDeclarationDecoder(MetricDeclarationDecoding):
    def __init__(
        self,
        decoder: StructuredModelDecoding[MetricDeclaration],
        expression_parser: WorkflowExpressionParsing,
        reference_parser: CollectionSourceReferenceParsing,
        condition_parser: ConditionParsing,
        reducer_decoder: CollectionMetricReducerDecoding,
        contract_assembler: MetricStepContractAssembling,
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._decoder = decoder
        self._expression_parser = expression_parser
        self._reference_parser = reference_parser
        self._condition_parser = condition_parser
        self._reducer_decoder = reducer_decoder
        self._contract_assembler = contract_assembler
        self._error_factory = error_factory

    def decode(self, raw: dict) -> MetricStepContract:
        step_id = raw.get("id") or "<unknown>"
        scoring = dict(raw.get("scoring") or {})
        source = scoring.pop("source", None)
        condition = scoring.pop("when", None)
        authored_reducer = scoring.pop("reducer", None)
        if source is None and condition is not None:
            raise self._error_factory.create(
                f"Metric step '{step_id}' scoring.when requires scoring.source"
            )
        if source is None and authored_reducer is not None:
            raise self._error_factory.create(
                f"Metric step '{step_id}' scoring.reducer requires scoring.source"
            )
        value = dict(raw.get("value") or {})
        metric_input = {
            "metric_id": raw.get("metric_id"),
            "observation_id": raw.get("observation_id", "value"),
            "value": value,
            "scoring": scoring,
            "unavailable_reason": raw.get("unavailable_reason"),
        }
        try:
            value_type = MetricValueType(value.get("type"))
            metric = None
        except (TypeError, ValueError):
            metric = self._decoder.decode(
                metric_input,
                f"metric step '{step_id}'",
            )
            value_type = metric.value.type
        reducer = self._reducer_decoder.decode(
            step_id,
            authored_reducer,
            value_type,
            source is not None,
        )
        if metric is None:
            metric = self._decoder.decode(
                metric_input,
                f"metric step '{step_id}'",
            )
        parsed_source = (
            self._reference_parser.parse(self._expression_parser.parse(source).value)
            if source is not None
            else None
        )
        parsed_condition = (
            self._condition_parser.parse(condition) if condition is not None else None
        )
        return self._contract_assembler.assemble(
            metric,
            parsed_source,
            parsed_condition,
            reducer,
        )
