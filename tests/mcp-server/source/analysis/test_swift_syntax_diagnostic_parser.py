"""Diagnostic policy can be tested without concrete parser nodes."""

import unittest
from unittest.mock import Mock

from source.analysis.swift_syntax_diagnostic_parser import SwiftSyntaxDiagnosticParser
from source.analysis.syntax_diagnostic_node_reading import SyntaxDiagnosticNodeReading
from tree_sitter import Point

"""
solid-name: TestSwiftSyntaxDiagnosticParser
solid-category: unit-test
solid-spec: [SPEC-063]
solid-description: Verifies recoverable syntax diagnostics using substitutable error and location evidence.
"""


class TestSwiftSyntaxDiagnosticParser(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = SwiftSyntaxDiagnosticParser()
        self.node = Mock(
            spec=SyntaxDiagnosticNodeReading,
            is_error=False,
            is_missing=False,
            has_error=False,
            child_count=0,
            type="type_identifier",
            start_point=Point(2, 4),
        )

    def test_valid_node_has_no_diagnostic(self) -> None:
        self.assertIsNone(self.parser.parse(self.node))

    def test_missing_node_records_kind_and_one_based_line(self) -> None:
        self.node.is_missing = True

        result = self.parser.parse(self.node)

        self.assertEqual(result.message, "Missing syntax token: type_identifier")
        self.assertEqual(result.line, 3)
        self.assertEqual(result.code, "swift.partial_parse")

    def test_explicit_error_is_reported(self) -> None:
        self.node.is_error = True

        self.assertEqual(
            self.parser.parse(self.node).message, "Unrecognized Swift syntax"
        )

    def test_opaque_missing_leaf_is_reported(self) -> None:
        self.node.has_error = True

        self.assertEqual(self.parser.parse(self.node).line, 3)

    def test_parent_error_flag_does_not_duplicate_its_child_diagnostic(self) -> None:
        self.node.has_error = True
        self.node.child_count = 1

        self.assertIsNone(self.parser.parse(self.node))
