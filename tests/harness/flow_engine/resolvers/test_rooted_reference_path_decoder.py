"""Protects authored field names and rooted-reference diagnostics."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.flow_validation_error import FlowValidationError
from harness.rooted_reference_path_decoder import RootedReferencePathDecoder
from harness.workflow_expression_parser import WorkflowExpressionParser


"""
solid-name: TestRootedReferencePathDecoder
solid-category: unit-test
solid-spec: [SPEC-059]
solid-description: Verifies rooted field decoding retains existing authored-name support and actionable validation context.
"""
class TestRootedReferencePathDecoder(unittest.TestCase):
    def setUp(self) -> None:
        self.decoder = RootedReferencePathDecoder("item", WorkflowExpressionParser())

    def test_keeps_hyphenated_authored_field_names(self) -> None:
        self.assertEqual(self.decoder.decode("{{item.resource-tags}}", "projection"), ["resource-tags"])

    def test_whole_item_projection_has_an_empty_path(self) -> None:
        self.assertEqual(self.decoder.decode("{{item}}", "projection"), [])

    def test_rejects_wrong_root_with_declared_context(self) -> None:
        with self.assertRaisesRegex(FlowValidationError, "projection must reference item"):
            self.decoder.decode("{{params.tags}}", "projection")

    def test_rejects_empty_field_components(self) -> None:
        with self.assertRaisesRegex(FlowValidationError, "projection must reference item"):
            self.decoder.decode("{{item..tags}}", "projection")

    def test_malformed_expression_keeps_declared_context(self) -> None:
        with self.assertRaisesRegex(FlowValidationError, "projection.*incomplete wrapper"):
            self.decoder.decode("{{item.tags}", "projection")
