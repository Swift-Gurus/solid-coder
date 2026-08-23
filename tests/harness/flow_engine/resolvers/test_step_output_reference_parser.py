"""Tests parsing authored local step-output references."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.step_output_reference import StepOutputReference
from harness.step_output_reference_parser import StepOutputReferenceParser
from harness.step_output_reference_syntax_error import (
    StepOutputReferenceSyntaxError,
)


"""
solid-name: TestStepOutputReferenceParser
solid-category: unit-test
solid-spec: [SPEC-030, SPEC-037]
solid-description: Verifies the shared expression boundary accepts local references and rejects runtime identity encodings.
"""
class TestStepOutputReferenceParser(unittest.TestCase):

    def test_parses_local_step_and_output_identity(self) -> None:
        reference = StepOutputReferenceParser().parse(
            "steps.inspect.outputs.finding"
        )

        self.assertEqual(
            reference,
            StepOutputReference(
                step_id="inspect",
                output_name="finding",
            ),
        )

    def test_parses_qualified_declaration_step_identity(self) -> None:
        reference = StepOutputReferenceParser().parse(
            "steps.file_review.prepare.outputs.finding"
        )

        self.assertEqual(
            reference,
            StepOutputReference(
                step_id="file_review.prepare",
                output_name="finding",
            ),
        )

    def test_rejects_incomplete_reference(self) -> None:
        with self.assertRaises(StepOutputReferenceSyntaxError):
            StepOutputReferenceParser().parse("steps.inspect.finding")


if __name__ == "__main__":
    unittest.main()
