"""Validates load-time workflow for-each reference rules."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.for_each_collection_validator import ForEachCollectionValidator
from harness.for_each_reference_parser import ForEachReferenceParser
from harness.for_each_reference_validator import ForEachReferenceValidator
from harness.models import FlowValidationError, OutputSpec, StepDef
from harness.step_dependency_reachability_checker import StepDependencyReachabilityChecker
from harness.step_output_reference import StepOutputReference
from harness.step_output_reference_parser import StepOutputReferenceParser
from harness.workflow_expression_parser import WorkflowExpressionParser


class TestForEachReferenceValidator(unittest.TestCase):
    def setUp(self) -> None:
        self.reference_parser = ForEachReferenceParser(
            expression_parser=WorkflowExpressionParser(),
            reference_parser=StepOutputReferenceParser(),
        )
        self.sut = ForEachCollectionValidator(
            target_validator=ForEachReferenceValidator(
                reachability_checker=StepDependencyReachabilityChecker(),
            ),
        )

    def test_accepts_array_output_from_a_transitive_dependency(self) -> None:
        steps = [
            self._source(),
            StepDef(id="middle", prompt="Middle", depends_on=["load"]),
            StepDef(
                id="review",
                prompt="Review {{item}}",
                depends_on=["middle"],
                for_each=self._reference("load", "files"),
            ),
        ]

        self.sut.validate_for_each_references(steps)

    def test_rejects_source_step_that_is_not_a_transitive_dependency(self) -> None:
        steps = [
            self._source(),
            StepDef(id="other", prompt="Other"),
            StepDef(
                id="review",
                prompt="Review {{item}}",
                depends_on=["other"],
                for_each=self._reference("load", "files"),
            ),
        ]

        with self.assertRaisesRegex(
            FlowValidationError,
            "must reference a transitive dependency",
        ):
            self.sut.validate_for_each_references(steps)

    def test_rejects_source_output_without_an_array_schema(self) -> None:
        source = StepDef(
            id="load",
            prompt="Load",
            outputs=[OutputSpec(
                name="files",
                type="data",
                schema={"type": "string"},
            )],
        )
        review = StepDef(
            id="review",
            prompt="Review {{item}}",
            depends_on=["load"],
            for_each=self._reference("load", "files"),
        )

        with self.assertRaisesRegex(
            FlowValidationError,
            "must declare an array schema",
        ):
            self.sut.validate_for_each_references([source, review])

    def test_rejects_malformed_for_each_expression(self) -> None:
        with self.assertRaisesRegex(
            FlowValidationError,
            "must use steps.<id>.outputs.<name>",
        ):
            self.reference_parser.parse("review", "files")

    def test_rejects_compound_runtime_step_identity(self) -> None:
        with self.assertRaisesRegex(
            FlowValidationError,
            "must use steps.<id>.outputs.<name>",
        ):
            self.reference_parser.parse(
                "review",
                "{{steps.review-1.inspect.outputs.files}}",
            )

    def test_restores_a_typed_reference_from_snapshot_fields(self) -> None:
        reference = self.reference_parser.parse(
            "review",
            {"step_id": "load", "output_name": "files"},
        )

        self.assertEqual(reference, self._reference("load", "files"))

    def _reference(self, step_id: str, output_name: str) -> StepOutputReference:
        return StepOutputReference(step_id=step_id, output_name=output_name)

    def _source(self) -> StepDef:
        return StepDef(
            id="load",
            prompt="Load",
            outputs=[OutputSpec(
                name="files",
                type="data",
                schema={"type": "array", "items": {"type": "string"}},
            )],
        )


if __name__ == "__main__":
    unittest.main()
