"""Tests durable rendering of collection metric reducer evidence."""

import sys
import unittest
from pathlib import Path

from pydantic import TypeAdapter

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.collection_metric_calculation import CollectionMetricCalculation
from harness.collection_metric_derivation_projection import (
    CollectionMetricDerivationProjection,
)
from harness.collection_metric_reducer import CollectionMetricReducer
from harness.collection_metric_reducer_type import CollectionMetricReducerType
from harness.collection_source_reference import CollectionSourceReference
from harness.comparison_condition import ComparisonCondition
from harness.condition_operator import ConditionOperator
from harness.metric_derivation_renderer import MetricDerivationRenderer
from harness.pydantic_type_adapter_encoder import PydanticTypeAdapterEncoder
from harness.step_output_reference import StepOutputReference
from harness.workflow_expression import WorkflowExpression
from harness.workflow_output_reference import WorkflowOutputReference


class StubConditionSerializer:
    def serialize(self, condition) -> dict:
        return {"serialized": condition.operator.value}


"""
solid-name: TestMetricDerivationRenderer
solid-category: unit-test
solid-spec: [SPEC-054]
solid-description: Verifies reducer-specific metric evidence survives durable rendering and typed decoding.
"""
class TestMetricDerivationRenderer(unittest.TestCase):
    def setUp(self) -> None:
        self.renderer = MetricDerivationRenderer(
            StubConditionSerializer(),
            PydanticTypeAdapterEncoder(TypeAdapter(CollectionSourceReference)),
        )

    def test_renders_ratio_indexes_and_zero_denominator_decision(self) -> None:
        condition = ComparisonCondition(
            reference=WorkflowExpression("item.selected"),
            operator=ConditionOperator.EQUALS,
            expected=True,
        )
        rendered = self.renderer.render(
            CollectionMetricCalculation(
                source=StepOutputReference("analyze", "entries"),
                reducer=CollectionMetricReducer(
                    type=CollectionMetricReducerType.RATIO,
                    empty_value=1.0,
                    numerator_condition=condition,
                    denominator_condition=condition,
                ),
                value=0.0,
                source_size=1,
                matched_indexes=[0],
                numerator_indexes=[],
                denominator_indexes=[],
                zero_denominator=True,
            )
        )

        projection = CollectionMetricDerivationProjection.model_validate(rendered)

        self.assertEqual(projection.kind, "collection_reducer")
        self.assertEqual(projection.reducer.type, CollectionMetricReducerType.RATIO)
        self.assertEqual(projection.reducer.empty_value, 1.0)
        self.assertEqual(projection.numerator_indexes, [])
        self.assertEqual(projection.denominator_indexes, [])
        self.assertTrue(projection.zero_denominator)

    def test_preserves_step_source_shape(self) -> None:
        rendered = self.renderer.render(CollectionMetricCalculation(
            source=StepOutputReference("classify", "items"),
        ))

        self.assertEqual(rendered["source"], {"step_id": "classify", "output_name": "items"})

    def test_preserves_workflow_source_discriminator(self) -> None:
        rendered = self.renderer.render(CollectionMetricCalculation(
            source=WorkflowOutputReference("children", "items"),
        ))

        self.assertEqual(rendered["source"], {
            "kind": "workflow_output", "workflow_alias": "children", "output_name": "items",
        })


if __name__ == "__main__":
    unittest.main()
