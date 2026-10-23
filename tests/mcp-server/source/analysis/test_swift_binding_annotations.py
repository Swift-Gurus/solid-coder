"""Checks annotations at exact declaration offsets, including sibling bindings."""

from unittest import TestCase

import tree_sitter_swift
from source.analysis.provenance.swift_binding_annotation_parser import (
    SwiftBindingAnnotationParser,
)
from tree_sitter import Language, Parser


class TestSwiftBindingAnnotations(TestCase):
    def annotation(self, source, name):
        tree = Parser(Language(tree_sitter_swift.language())).parse(source.encode())
        node = SwiftBindingAnnotationParser(tree).parse(
            source.encode().index(name.encode())
        )
        return node.text.decode() if node is not None else None

    def test_parameter_annotation(self):
        self.assertEqual(
            self.annotation("func use(_ value: any Service) {}", "value"), "any Service"
        )

    def test_property_annotation(self):
        self.assertEqual(
            self.annotation("struct A { var value: Service { provider() } }", "value"),
            ": Service",
        )

    def test_inferred_binding_does_not_borrow_its_siblings_annotation(self):
        source = "let first = 1, second: Service = provider()"
        self.assertIsNone(self.annotation(source, "first"))
        self.assertEqual(self.annotation(source, "second"), ": Service")

    def test_inferred_binding_is_unresolved(self):
        self.assertIsNone(self.annotation("let value = provider()", "value"))

    def test_non_binding_declaration_is_unresolved(self):
        self.assertIsNone(self.annotation("struct Service {}", "Service"))
