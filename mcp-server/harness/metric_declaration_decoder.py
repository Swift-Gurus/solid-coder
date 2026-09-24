"""Decodes workflow metric fields into a typed declaration."""

from harness.collection_metric_calculation import CollectionMetricCalculation
from harness.condition_parsing import ConditionParsing
from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.metric_declaration import MetricDeclaration
from harness.metric_declaration_decoding import MetricDeclarationDecoding
from harness.metric_step_contract import MetricStepContract
from harness.metric_value_type import MetricValueType
from harness.step_output_reference_parsing import StepOutputReferenceParsing
from harness.structured_model_decoding import StructuredModelDecoding
from harness.workflow_expression_parsing import WorkflowExpressionParsing


"""
solid-name: MetricDeclarationDecoder
solid-category: boundary-adapter
solid-spec: [SPEC-039]
solid-description: Maps metric fields from one workflow step into a validated metric declaration.
"""
class MetricDeclarationDecoder(MetricDeclarationDecoding):
    def __init__(
        self,
        decoder: StructuredModelDecoding[MetricDeclaration],
        expression_parser: WorkflowExpressionParsing,
        reference_parser: StepOutputReferenceParsing,
        condition_parser: ConditionParsing,
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._decoder = decoder
        self._expression_parser = expression_parser
        self._reference_parser = reference_parser
        self._condition_parser = condition_parser
        self._error_factory = error_factory

    def decode(self, raw: dict) -> MetricStepContract:
        step_id = raw.get("id") or "<unknown>"
        scoring = dict(raw.get("scoring") or {})
        source = scoring.pop("source", None)
        condition = scoring.pop("when", None)
        if source is None and condition is not None:
            raise self._error_factory.create(
                f"Metric step '{step_id}' scoring.when requires scoring.source"
            )
        calculation = (
            CollectionMetricCalculation(
                source=self._reference_parser.parse(
                    self._expression_parser.parse(source).value
                ),
                condition=(
                    self._condition_parser.parse(condition)
                    if condition is not None
                    else None
                ),
            )
            if source is not None
            else None
        )
        value = dict(raw.get("value") or {})
        if (
            calculation is not None
            and value.get("type") != MetricValueType.INTEGER.value
        ):
            raise self._error_factory.create(
                f"Metric step '{step_id}' collection-backed metric value "
                "must be an integer"
            )
        metric = self._decoder.decode(
            {
                "metric_id": raw.get("metric_id"),
                "observation_id": raw.get("observation_id", "value"),
                "value": value,
                "scoring": scoring,
            },
            f"metric step '{step_id}'",
        )
        return MetricStepContract(metric=metric, calculation=calculation)
