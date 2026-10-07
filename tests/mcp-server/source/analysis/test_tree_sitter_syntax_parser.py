"""Qualifies the shared syntax parser against Swift and TypeScript grammars."""

import unittest

import tree_sitter_swift
import tree_sitter_typescript
from tree_sitter import Language, Parser

from source.analysis.tree_sitter_syntax_parser import TreeSitterSyntaxParser


"""
solid-name: TestTreeSitterSyntaxParser
solid-category: unit-test
solid-spec: [SPEC-057]
solid-description: Verifies shared syntax parsing preserves declaration facts and incomplete-buffer diagnostics across language grammars.
"""
class TestTreeSitterSyntaxParser(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = TreeSitterSyntaxParser(Parser(Language(tree_sitter_swift.language())))

    def test_swift_overloads_preserve_parameter_labels_and_types(self) -> None:
        tree = self.parser.parse(
            "protocol Loading {\n"
            "  func load(id: String) async throws -> String\n"
            "  func load(id: Int) -> String\n"
            "}\n"
        )

        self.assertFalse(tree.root_node.has_error)
        declaration = tree.root_node.named_children[0]
        body = declaration.child_by_field_name("body")
        methods = body.named_children
        parameters = [
            child
            for method in methods
            for child in method.named_children
            if child.type == "parameter"
        ]
        self.assertEqual(
            [[part.text.decode("utf-8") for part in parameter.children_by_field_name("name")]
             for parameter in parameters],
            [["id", "String"], ["id", "Int"]],
        )

    def test_swift_conformance_and_separate_extension_preserve_owner_names(self) -> None:
        declaration_tree = self.parser.parse("struct Store: Loading {}\n")
        extension_tree = self.parser.parse("extension Store { func load() {} }\n")

        self.assertFalse(declaration_tree.root_node.has_error)
        self.assertFalse(extension_tree.root_node.has_error)
        declaration = declaration_tree.root_node.named_children[0]
        inheritance = next(
            child for child in declaration.named_children
            if child.type == "inheritance_specifier"
        )
        self.assertEqual(inheritance.child_by_field_name("inherits_from").text, b"Loading")
        extension = extension_tree.root_node.named_children[0]
        self.assertEqual(extension.child_by_field_name("name").text, b"Store")
        self.assertEqual(extension.children[0].text, b"extension")

    def test_swift_members_preserve_associated_types_properties_and_visibility(self) -> None:
        tree = self.parser.parse(
            "protocol Loading { associatedtype Item; var item: Item { get } }\n"
            "extension Loading { private func hidden() {}; fileprivate func local() {} }\n"
        )

        self.assertFalse(tree.root_node.has_error)
        declaration, extension = tree.root_node.named_children
        self.assertEqual(
            [member.type for member in declaration.child_by_field_name("body").named_children],
            ["associatedtype_declaration", "protocol_property_declaration"],
        )
        self.assertEqual(
            [member.named_children[0].text for member in extension.child_by_field_name("body").named_children],
            [b"private", b"fileprivate"],
        )

    def test_swift_generic_constraints_are_not_lost(self) -> None:
        tree = self.parser.parse(
            "extension Store where Item: Equatable {\n"
            "  func load<T>(_ value: T) -> T where T: Hashable { value }\n"
            "}\n"
        )

        self.assertFalse(tree.root_node.has_error)
        extension = tree.root_node.named_children[0]
        self.assertIn(b"where Item: Equatable", [child.text for child in extension.named_children])
        method = extension.child_by_field_name("body").named_children[0]
        self.assertIn(b"where T: Hashable", [child.text for child in method.named_children])

    def test_incomplete_buffer_retains_parse_error_without_becoming_empty_success(self) -> None:
        tree = self.parser.parse("protocol Loading { func load(id: String)\n")

        self.assertTrue(tree.root_node.has_error)
        self.assertGreater(tree.root_node.named_child_count, 0)

    def test_unicode_ranges_use_the_original_utf8_buffer(self) -> None:
        source = "// café 😀\nprotocol Chargement { func télécharger() }\n"
        tree = self.parser.parse(source)
        declaration = tree.root_node.named_children[-1]
        method = declaration.child_by_field_name("body").named_children[0]
        name = method.child_by_field_name("name")

        self.assertFalse(tree.root_node.has_error)
        self.assertEqual(name.text.decode("utf-8"), "télécharger")
        self.assertEqual(source.encode("utf-8")[name.start_byte:name.end_byte], name.text)
        self.assertEqual(name.start_point.row, 1)

    def test_same_parser_adapter_supports_typescript_without_swift_special_cases(self) -> None:
        parser = TreeSitterSyntaxParser(Parser(Language(tree_sitter_typescript.language_typescript())))
        tree = parser.parse(
            "interface Loading { load(id: string): string; }\n"
            "class Store implements Loading { load(id: string): string { return id; } }\n"
        )

        self.assertFalse(tree.root_node.has_error)
        interface, declaration = tree.root_node.named_children
        self.assertEqual(interface.type, "interface_declaration")
        self.assertEqual(interface.child_by_field_name("name").text, b"Loading")
        self.assertEqual(declaration.type, "class_declaration")
        self.assertEqual(declaration.child_by_field_name("name").text, b"Store")
