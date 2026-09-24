"""Decodes sealed collection metric reducer declarations."""

from __future__ import annotations

from collections.abc import Mapping

from harness.collection_metric_reducer import CollectionMetricReducer
from harness.collection_metric_reducer_decoding import (
    CollectionMetricReducerDecoding,
)
from harness.collection_metric_reducer_type import CollectionMetricReducerType
from harness.condition_parsing import ConditionParsing
from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.metric_value_type import MetricValueType
from harness.workflow_expression_parsing import WorkflowExpressionParsing


"""
solid-name: CollectionMetricReducerDecoder
solid-category: boundary
solid-spec: [SPEC-054]
solid-description: Decodes validated deterministic reducers from workflow input.
"""
class CollectionMetricReducerDecoder(CollectionMetricReducerDecoding):
    def __init__(
        self,
        expression_parser: WorkflowExpressionParsing,
        condition_parser: ConditionParsing,
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._expression_parser = expression_parser
        self._condition_parser = condition_parser
        self._error_factory = error_factory

    def decode(
        self,
        step_id: str,
        raw: object,
        metric_value_type: MetricValueType,
        collection_backed: bool,
    ) -> CollectionMetricReducer | None:
        if raw is None:
            if collection_backed and metric_value_type != MetricValueType.INTEGER:
                raise self._error_factory.create(
                    f"Metric step '{step_id}' collection-backed metric value "
                    "must be an integer"
                )
            return None
        if not isinstance(raw, Mapping):
            raise self._error_factory.create(
                f"Metric step '{step_id}' scoring.reducer must be an object"
            )
        reducer_type = self._type(step_id, raw.get("type"))
        self._validate_fields(step_id, reducer_type, set(raw.keys()))
        self._validate_metric_type(step_id, reducer_type, metric_value_type)
        if reducer_type == CollectionMetricReducerType.RATIO:
            return CollectionMetricReducer(
                type=reducer_type,
                numerator_condition=self._condition(
                    step_id,
                    raw.get("numerator_when"),
                    "numerator_when",
                ),
                denominator_condition=self._condition(
                    step_id,
                    raw.get("denominator_when"),
                    "denominator_when",
                ),
            )
        value = raw.get("value")
        if value is None:
            raise self._error_factory.create(
                f"Metric step '{step_id}' {reducer_type.value} reducer "
                "requires a value reference"
            )
        expression = self._expression_parser.parse(value)
        if not expression.value.startswith("item."):
            raise self._error_factory.create(
                f"Metric step '{step_id}' reducer value must reference item"
            )
        return CollectionMetricReducer(
            type=reducer_type,
            value=expression,
        )

    def _type(
        self,
        step_id: str,
        raw_type: object,
    ) -> CollectionMetricReducerType:
        try:
            return CollectionMetricReducerType(raw_type)
        except (TypeError, ValueError) as error:
            raise self._error_factory.create(
                f"Metric step '{step_id}' declares unsupported reducer "
                f"'{raw_type}'"
            ) from error

    def _validate_fields(
        self,
        step_id: str,
        reducer_type: CollectionMetricReducerType,
        fields: set[object],
    ) -> None:
        allowed = (
            {"type", "numerator_when", "denominator_when"}
            if reducer_type == CollectionMetricReducerType.RATIO
            else {"type", "value"}
        )
        unknown = sorted(str(field) for field in fields - allowed)
        if not unknown:
            return
        if reducer_type == CollectionMetricReducerType.RATIO and "value" in unknown:
            raise self._error_factory.create(
                f"Metric step '{step_id}' ratio reducer must not declare "
                "a value reference"
            )
        raise self._error_factory.create(
            f"Metric step '{step_id}' {reducer_type.value} reducer has "
            f"unsupported fields: {', '.join(unknown)}"
        )

    def _validate_metric_type(
        self,
        step_id: str,
        reducer_type: CollectionMetricReducerType,
        metric_value_type: MetricValueType,
    ) -> None:
        if (
            reducer_type == CollectionMetricReducerType.DISTINCT_COUNT
            and metric_value_type != MetricValueType.INTEGER
        ):
            raise self._error_factory.create(
                f"Metric step '{step_id}' distinct_count reducer metric value "
                "must be an integer"
            )
        if (
            reducer_type == CollectionMetricReducerType.RATIO
            and metric_value_type != MetricValueType.NUMBER
        ):
            raise self._error_factory.create(
                f"Metric step '{step_id}' ratio reducer metric value must be "
                "a number"
            )
        if (
            reducer_type in {
                CollectionMetricReducerType.MAXIMUM,
                CollectionMetricReducerType.MINIMUM,
            }
            and metric_value_type not in {
                MetricValueType.INTEGER,
                MetricValueType.NUMBER,
            }
        ):
            raise self._error_factory.create(
                f"Metric step '{step_id}' {reducer_type.value} reducer metric "
                "value must be numeric"
            )

    def _condition(
        self,
        step_id: str,
        raw: object,
        field_name: str,
    ):
        if raw is None:
            raise self._error_factory.create(
                f"Metric step '{step_id}' ratio reducer requires {field_name}"
            )
        return self._condition_parser.parse(raw)
