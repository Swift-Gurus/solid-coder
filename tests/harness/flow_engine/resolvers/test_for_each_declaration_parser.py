"""Validates typed individual and batched for-each declarations."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.for_each_declaration import ForEachDeclaration
from harness.for_each_declaration_parser import ForEachDeclarationParser
from harness.for_each_mode import ForEachMode
from harness.for_each_reference_parser import ForEachReferenceParser
from harness.models import FlowValidationError
from harness.step_output_reference import StepOutputReference
from harness.step_output_reference_parser import StepOutputReferenceParser
from harness.workflow_expression import WorkflowExpression
from harness.workflow_expression_parser import WorkflowExpressionParser


"""
solid-name: TestForEachDeclarationParser
solid-category: unit-test
solid-spec: [SPEC-042]
solid-description: Proves workflow YAML decodes for-each source, model presentation mode, and domain label into one typed declaration.
"""
class TestForEachDeclarationParser(unittest.TestCase):
    def setUp(self) -> None:
        expression_parser = WorkflowExpressionParser()
        self.sut = ForEachDeclarationParser(
            reference_parser=ForEachReferenceParser(
                expression_parser=expression_parser,
                reference_parser=StepOutputReferenceParser(),
            ),
            expression_parser=expression_parser,
        )

    def test_scalar_syntax_preserves_individual_mode(self) -> None:
        declaration = self.sut.parse(
            "review",
            "{{steps.prepare.outputs.units}}",
        )

        self.assertEqual(
            declaration,
            ForEachDeclaration(
                source=StepOutputReference(
                    step_id="prepare",
                    output_name="units",
                ),
                mode=ForEachMode.INDIVIDUAL,
            ),
        )

    def test_object_syntax_decodes_batch_mode_and_typed_label(self) -> None:
        declaration = self.sut.parse(
            "review",
            {
                "source": "{{steps.prepare.outputs.units}}",
                "mode": "batch",
                "label": "{{item.target.name}}",
            },
        )

        self.assertEqual(
            declaration,
            ForEachDeclaration(
                source=StepOutputReference(
                    step_id="prepare",
                    output_name="units",
                ),
                mode=ForEachMode.BATCH,
                label=WorkflowExpression(value="item.target.name"),
            ),
        )

    def test_rejects_batch_mode_without_a_label(self) -> None:
        with self.assertRaisesRegex(
            FlowValidationError,
            "batch.*label",
        ):
            self.sut.parse(
                "review",
                {
                    "source": "{{steps.prepare.outputs.units}}",
                    "mode": "batch",
                },
            )

    def test_rejects_unknown_mode(self) -> None:
        with self.assertRaisesRegex(
            FlowValidationError,
            "mode.*individual.*batch",
        ):
            self.sut.parse(
                "review",
                {
                    "source": "{{steps.prepare.outputs.units}}",
                    "mode": "parallel",
                    "label": "{{item.target.name}}",
                },
            )


if __name__ == "__main__":
    unittest.main()
