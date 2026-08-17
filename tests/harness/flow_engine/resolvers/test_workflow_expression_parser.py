"""Validates workflow-expression decoding at definition and snapshot boundaries."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.flow_validation_error import FlowValidationError  # noqa: E402
from harness.workflow_expression import WorkflowExpression  # noqa: E402
from harness.workflow_expression_parser import WorkflowExpressionParser  # noqa: E402


"""
solid-name: TestWorkflowExpressionParser
solid-category: unit-test
solid-spec: [SPEC-037]
solid-description: Proves authored and snapshotted workflow expressions become normalized typed values at their input boundary.
"""
class TestWorkflowExpressionParser(unittest.TestCase):

    def setUp(self) -> None:
        self.sut = WorkflowExpressionParser()

    def test_normalizes_an_authored_wrapped_expression_once(self) -> None:
        self.assertEqual(
            self.sut.parse("  {{ item.path }}  "),
            WorkflowExpression(value="item.path"),
        )

    def test_restores_a_typed_expression_from_snapshot_fields(self) -> None:
        self.assertEqual(
            self.sut.parse({"value": "item.path"}),
            WorkflowExpression(value="item.path"),
        )

    def test_rejects_an_empty_expression(self) -> None:
        with self.assertRaises(FlowValidationError):
            self.sut.parse(" {{  }} ")


if __name__ == "__main__":
    unittest.main()
