"""Renders collection metric derivation audit payloads."""

from typing import Optional

from harness.collection_metric_calculation import CollectionMetricCalculation
from harness.condition_serializing import ConditionSerializing
from harness.metric_derivation_rendering import MetricDerivationRendering


"""
solid-name: MetricDerivationRenderer
solid-category: boundary
solid-spec: [SPEC-053, SPEC-054]
solid-description: Renders durable collection metric derivation audit payloads.
"""
class MetricDerivationRenderer(MetricDerivationRendering):
    def __init__(self, condition_serializer: ConditionSerializing) -> None:
        self._condition_serializer = condition_serializer

    def render(
        self,
        calculation: Optional[CollectionMetricCalculation],
    ) -> Optional[dict]:
        if calculation is None:
            return None
        condition = calculation.condition
        reducer = calculation.reducer
        return {
            "kind": (
                "collection_reducer"
                if reducer is not None
                else "collection_count"
            ),
            "source": {
                "step_id": calculation.source.step_id,
                "output_name": calculation.source.output_name,
            },
            "source_size": calculation.source_size,
            "condition": (
                self._condition_serializer.serialize(condition)
                if condition is not None
                else None
            ),
            "matched_indexes": calculation.matched_indexes,
            "excluded_indexes": calculation.excluded_indexes,
            "condition_evidence": [
                evidence.model_dump(mode="json")
                for evidence in calculation.condition_evidence
            ],
            "reducer": (
                {
                    "type": reducer.type.value,
                    "value": (
                        reducer.value.value
                        if reducer.value is not None
                        else None
                    ),
                    "numerator_when": (
                        self._condition_serializer.serialize(
                            reducer.numerator_condition
                        )
                        if reducer.numerator_condition is not None
                        else None
                    ),
                    "denominator_when": (
                        self._condition_serializer.serialize(
                            reducer.denominator_condition
                        )
                        if reducer.denominator_condition is not None
                        else None
                    ),
                }
                if reducer is not None
                else None
            ),
            "projection_evidence": [
                {"index": evidence.index, "value": evidence.value}
                for evidence in calculation.projection_evidence
            ],
            "distinct_indexes": calculation.distinct_indexes,
            "numerator_indexes": calculation.numerator_indexes,
            "denominator_indexes": calculation.denominator_indexes,
            "numerator_condition_evidence": [
                evidence.model_dump(mode="json")
                for evidence in calculation.numerator_condition_evidence
            ],
            "denominator_condition_evidence": [
                evidence.model_dump(mode="json")
                for evidence in calculation.denominator_condition_evidence
            ],
            "zero_denominator": calculation.zero_denominator,
        }
