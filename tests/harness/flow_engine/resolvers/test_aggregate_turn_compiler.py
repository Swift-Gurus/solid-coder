"""Tests compact aggregate prompt and response-schema compilation."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.aggregate_assignment import AggregateAssignment
from harness.aggregate_item_schema_builder import AggregateItemSchemaBuilder
from harness.aggregate_prompt_renderer import AggregatePromptRenderer
from harness.aggregate_response_schema_builder import AggregateResponseSchemaBuilder
from harness.aggregate_step_schema_builder import AggregateStepSchemaBuilder
from harness.aggregate_turn_compiler import AggregateTurnCompiler
from harness.aggregate_workflow_schema_builder import AggregateWorkflowSchemaBuilder
from harness.authored_step_coordinate import AuthoredStepCoordinate
from harness.output_spec import OutputSpec
from harness.output_spec_schema_serializer import OutputSpecSchemaSerializer
from harness.strict_object_schema_builder import StrictObjectSchemaBuilder


"""
solid-name: TestAggregateTurnCompiler
solid-category: unit-test
solid-spec: [SPEC-045]
solid-description: Proves aggregate turns deduplicate typed instructions and preserve exact assignment output contracts.
"""
class TestAggregateTurnCompiler(unittest.TestCase):
    def setUp(self) -> None:
        object_schema_builder = StrictObjectSchemaBuilder()
        self.sut = AggregateTurnCompiler(
            prompt_renderer=AggregatePromptRenderer(),
            schema_builder=AggregateResponseSchemaBuilder(
                item_schema_builder=AggregateItemSchemaBuilder(
                    workflow_schema_builder=AggregateWorkflowSchemaBuilder(
                        step_schema_builder=AggregateStepSchemaBuilder(
                            output_serializer=OutputSpecSchemaSerializer(),
                            object_schema_builder=object_schema_builder,
                        ),
                        object_schema_builder=object_schema_builder,
                    ),
                    object_schema_builder=object_schema_builder,
                ),
                object_schema_builder=object_schema_builder,
            ),
        )

    def test_renders_ordered_authored_sections_once_for_repeated_assignments(self) -> None:
        inspect = AuthoredStepCoordinate(
            workflow_id="alpha",
            step_id="inspect",
            prompt="Inspect the supplied item.",
            outputs=[OutputSpec(name="analysis", type="data")],
        )
        decide = AuthoredStepCoordinate(
            workflow_id="alpha",
            step_id="decide",
            prompt="Decide whether it passes.",
            outputs=[
                OutputSpec(
                    name="value",
                    type="data",
                    schema={"type": "integer"},
                )
            ],
        )
        assignments = [
            AggregateAssignment(
                item_label="A",
                workflow_alias="alpha_rule",
                instance_id="internal-alpha-1",
                steps=[inspect, decide],
            ),
            AggregateAssignment(
                item_label="B",
                workflow_alias="alpha_rule",
                instance_id="internal-alpha-2",
                steps=[inspect, decide],
            ),
        ]

        compiled = self.sut.compile(assignments)

        self.assertEqual(compiled.prompt.count(inspect.prompt), 1)
        self.assertEqual(compiled.prompt.count(decide.prompt), 1)
        self.assertLess(compiled.prompt.index(inspect.prompt), compiled.prompt.index(decide.prompt))
        self.assertIn("A: alpha_rule", compiled.prompt)
        self.assertIn("B: alpha_rule", compiled.prompt)
        self.assertNotIn("internal-alpha-1", compiled.prompt)
        self.assertNotIn("internal-alpha-2", compiled.prompt)

    def test_renders_generic_applicability_matrix_for_different_workflows(self) -> None:
        alpha = AuthoredStepCoordinate(
            workflow_id="alpha",
            step_id="assess",
            prompt="Apply alpha.",
            outputs=[OutputSpec(name="value", type="data")],
        )
        beta = AuthoredStepCoordinate(
            workflow_id="beta",
            step_id="assess",
            prompt="Apply beta.",
            outputs=[OutputSpec(name="value", type="data")],
        )

        compiled = self.sut.compile([
            AggregateAssignment("A", "alpha", "alpha-1", [alpha]),
            AggregateAssignment("B", "alpha", "alpha-2", [alpha]),
            AggregateAssignment("B", "beta", "beta-2", [beta]),
        ])

        self.assertIn("A: alpha", compiled.prompt)
        self.assertIn("B: alpha, beta", compiled.prompt)
        self.assertNotIn("package", compiled.prompt.lower())
        self.assertNotIn("unit", compiled.prompt.lower())

    def test_generates_exact_item_workflow_step_output_schema(self) -> None:
        analyze = AuthoredStepCoordinate(
            workflow_id="alpha",
            step_id="analyze",
            prompt="Analyze.",
            outputs=[
                OutputSpec(
                    name="value",
                    type="data",
                    schema={"type": "object", "required": ["count"]},
                )
            ],
        )
        measure = AuthoredStepCoordinate(
            workflow_id="alpha",
            step_id="measure",
            prompt="Measure.",
            outputs=[
                OutputSpec(
                    name="value",
                    type="data",
                    schema={"type": "integer"},
                )
            ],
        )

        compiled = self.sut.compile([
            AggregateAssignment("Item A", "alpha", "alpha-1", [analyze, measure]),
        ])

        item_schema = compiled.schema["properties"]["Item A"]
        workflow_schema = item_schema["properties"]["alpha"]
        self.assertEqual(
            set(workflow_schema["required"]),
            {"analyze", "measure"},
        )
        self.assertEqual(
            workflow_schema["properties"]["analyze"]["properties"]["value"],
            {"type": "object", "required": ["count"]},
        )
        self.assertEqual(
            workflow_schema["properties"]["measure"]["properties"]["value"],
            {"type": "integer"},
        )
        self.assertFalse(compiled.schema["additionalProperties"])
        self.assertFalse(item_schema["additionalProperties"])
        self.assertFalse(workflow_schema["additionalProperties"])

    def test_serializes_unconstrained_data_and_file_outputs(self) -> None:
        collect = AuthoredStepCoordinate(
            workflow_id="alpha",
            step_id="collect",
            prompt="Collect.",
            outputs=[
                OutputSpec(name="value", type="data"),
                OutputSpec(name="artifact", type="file"),
            ],
        )

        compiled = self.sut.compile([
            AggregateAssignment("Item A", "alpha", "alpha-1", [collect]),
        ])
        outputs = compiled.schema["properties"]["Item A"]["properties"][
            "alpha"
        ]["properties"]["collect"]["properties"]

        self.assertEqual(outputs["value"], {})
        self.assertEqual(outputs["artifact"], {"type": "string"})


if __name__ == "__main__":
    unittest.main()
