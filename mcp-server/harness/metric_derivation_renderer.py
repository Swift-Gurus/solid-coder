"""Renders collection metric derivation audit payloads."""

from typing import Optional

from harness.collection_metric_calculation import CollectionMetricCalculation
from harness.condition_serializing import ConditionSerializing
from harness.metric_derivation_rendering import MetricDerivationRendering


"""
solid-name: MetricDerivationRenderer
solid-category: boundary
solid-spec: [SPEC-053]
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
        return {
            "kind": "collection_count",
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
        }
