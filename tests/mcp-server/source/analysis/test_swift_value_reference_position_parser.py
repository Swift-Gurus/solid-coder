"""Locates the inspected value's symbol without selecting receivers or arguments."""

from unittest import TestCase

from tree_sitter import Language, Parser
import tree_sitter_swift

from source.analysis.provenance.swift_value_reference_position_parser import SwiftValueReferencePositionParser


class TestSwiftValueReferencePositionParser(TestCase):
    def test_identifiers_and_call_targets_have_exact_byte_positions(self):
        parser = SwiftValueReferencePositionParser()
        syntax = Parser(Language(tree_sitter_swift.language()))
        for source, identifier in [
            ("service", "service"),
            ("cache.object(forKey: key as NSString)", "object"),
            ("provider.make()", "make"),
            ("provider?.make()", "make"),
            ("factory.provider().make()", "make"),
            ("make()", "make"),
        ]:
            with self.subTest(source=source):
                node = syntax.parse(source.encode()).root_node.named_children[0]
                self.assertEqual(parser.parse(node), source.encode().rindex(identifier.encode()))

    def test_compound_non_call_operands_remain_unresolved(self):
        parser = SwiftValueReferencePositionParser()
        syntax = Parser(Language(tree_sitter_swift.language()))
        for source in ["left + right", "(left, right)", "42", "provider.value"]:
            with self.subTest(source=source):
                self.assertIsNone(parser.parse(syntax.parse(source.encode()).root_node.named_children[0]))
