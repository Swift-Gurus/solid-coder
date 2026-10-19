"""Checks bounded explicit-type positions without semantic guessing."""

from unittest import TestCase
from types import SimpleNamespace

from tree_sitter import Language, Parser
import tree_sitter_swift

from source.analysis.provenance.swift_type_reference_position_parser import SwiftTypeReferencePositionParser
from source.analysis.tree_sitter_nodes_parser import TreeSitterNodesParser


class TestSwiftSemanticTypePositions(TestCase):
    def setUp(self):
        self.syntax = Parser(Language(tree_sitter_swift.language()))
        self.nodes = TreeSitterNodesParser(frozenset(), frozenset())
        self.positions = SwiftTypeReferencePositionParser(self.nodes)

    def position(self, annotation):
        source = f"func inspect(_ value: {annotation}) {{}}"
        root = self.syntax.parse(source.encode()).root_node
        parameter = next(node for node in self.nodes.parse(root) if node.type == "parameter")
        return SimpleNamespace(position=self.positions.parse(parameter), source=source)

    def test_simple_existential_and_qualified_type_positions(self):
        for annotation in ["Service", "any Service", "Module.Service", "Service?"]:
            with self.subTest(annotation=annotation):
                result = self.position(annotation)
                self.assertEqual(result.position, result.source.encode().index(b"Service"))

    def test_composite_and_generic_types_are_not_guessed(self):
        for annotation in ["A & B", "Container<Service>", "(Service, Other)", "(Service) -> Other"]:
            with self.subTest(annotation=annotation):
                self.assertIsNone(self.position(annotation).position)

    def test_exact_destination_range_can_select_the_type_identifier_leaf(self):
        source = "value as? Concrete"
        tree = self.syntax.parse(source.encode())
        node = tree.root_node.descendant_for_byte_range(source.index("Concrete"), len(source))
        self.assertEqual(node.type, "type_identifier")
        self.assertEqual(self.positions.parse(node), source.index("Concrete"))
