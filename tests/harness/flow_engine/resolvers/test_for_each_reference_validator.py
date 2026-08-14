"""Validates load-time workflow for-each reference rules."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.for_each_reference_parser import ForEachReferenceParser
from harness.for_each_reference_validator import ForEachReferenceValidator
from harness.models import FlowValidationError, OutputSpec, StepDef
from harness.step_dependency_reachability_checker import StepDependencyReachabilityChecker


class TestForEachReferenceValidator(unittest.TestCase):
    def setUp(self) -> None:
        self.sut = ForEachReferenceValidator(
            reference_parser=ForEachReferenceParser(),
            reachability_checker=StepDependencyReachabilityChecker(),
        )

    def test_accepts_array_output_from_a_transitive_dependency(self) -> None:
        steps = [
            self._source(),
            StepDef(id="middle", prompt="Middle", depends_on=["load"]),
            StepDef(
                id="review",
                prompt="Review {{item}}",
                depends_on=["middle"],
                for_each="{{steps.load.outputs.files}}",
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
                for_each="{{steps.load.outputs.files}}",
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
            for_each="{{steps.load.outputs.files}}",
        )

        with self.assertRaisesRegex(
            FlowValidationError,
            "must declare an array schema",
        ):
            self.sut.validate_for_each_references([source, review])

    def test_rejects_malformed_for_each_expression(self) -> None:
        review = StepDef(
            id="review",
            prompt="Review {{item}}",
            depends_on=["load"],
            for_each="files",
        )

        with self.assertRaisesRegex(
            FlowValidationError,
            "must use steps.<id>.outputs.<name>",
        ):
            self.sut.validate_for_each_references([self._source(), review])

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
