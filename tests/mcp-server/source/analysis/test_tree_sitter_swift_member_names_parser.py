"""Protects declared names from unrelated grammar name fields."""

import unittest

import tree_sitter_swift
from source.analysis.tree_sitter_swift_binding_names_parser import (
    TreeSitterSwiftBindingNamesParser,
)
from source.analysis.tree_sitter_swift_member_names_parser import (
    TreeSitterSwiftMemberNamesParser,
)
from tree_sitter import Language, Parser

"""
solid-name: TestTreeSitterSwiftMemberNamesParser
solid-category: unit-test
solid-spec: [SPEC-057, SPEC-062]
solid-description: Verifies that member names exclude return types and associated-type constraints while preserving all property bindings.
"""


class TestTreeSitterSwiftMemberNamesParser(unittest.TestCase):
    def setUp(self) -> None:
        self.syntax = Parser(Language(tree_sitter_swift.language()))
        self.names = TreeSitterSwiftMemberNamesParser(
            TreeSitterSwiftBindingNamesParser()
        )

    def test_return_types_and_constraints_are_not_member_names(self) -> None:
        root = self.syntax.parse(
            b"protocol P { func read() -> Int; associatedtype Item: Sequence }",
        ).root_node
        body = root.named_children[0].child_by_field_name("body")
        names = [
            name.text.decode()
            for member in body.named_children
            for name in self.names.parse(member)
        ]

        self.assertEqual(names, ["read", "Item"])

    def test_multiple_and_nested_bindings_keep_every_declared_name(self) -> None:
        root = self.syntax.parse(
            b"var x = 1, y = 2; var (a, (b, c)) = (1, (2, 3))"
        ).root_node
        names = [
            name.text.decode()
            for member in root.named_children
            for name in self.names.parse(member)
        ]

        self.assertEqual(names, ["x", "y", "a", "b", "c"])
