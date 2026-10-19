"""Checks semantic return references without guessing ownership from names."""

from unittest import TestCase

from source.analysis.provenance.native.swift_return_type_reference_parser import SwiftReturnTypeReferenceParser


class TestSwiftReturnTypeReferenceParser(TestCase):
    def setUp(self):
        self.parser = SwiftReturnTypeReferenceParser()

    def test_uses_return_reference_not_parameter_reference(self):
        declaration = (
            '<decl.function.method.instance><decl.var.parameter.type>'
            '<ref.class usr="parameter">Key</ref.class></decl.var.parameter.type>'
            '<decl.function.returntype><ref.typealias usr="result">AnyObject</ref.typealias>?'
            '</decl.function.returntype></decl.function.method.instance>'
        )
        self.assertEqual(self.parser.parse(declaration), "result")

    def test_preserves_existential_contract_identity(self):
        self.assertEqual(self.parser.parse(
            '<decl.function.free><decl.function.returntype>any '
            '<ref.protocol usr="service">Service</ref.protocol>'
            '</decl.function.returntype></decl.function.free>'
        ), "service")

    def test_does_not_reduce_composite_results_to_one_reference(self):
        bodies = [
            '<ref.struct usr="array">Array</ref.struct>&lt;<ref.class usr="owned">Owned</ref.class>&gt;',
            '(<ref.class usr="owned">Owned</ref.class>, <ref.class usr="owned">Owned</ref.class>)',
            '() -&gt; <ref.class usr="owned">Owned</ref.class>',
            'some <ref.protocol usr="service">Service</ref.protocol>',
            '<ref.generic_type_param usr="generic">T</ref.generic_type_param>',
        ]
        for body in bodies:
            with self.subTest(body=body):
                self.assertIsNone(self.parser.parse(
                    '<decl.function.free><decl.function.returntype>' + body
                    + '</decl.function.returntype></decl.function.free>'
                ))

    def test_missing_malformed_or_ambiguous_evidence_is_unresolved(self):
        for declaration in [
            "", "not XML", '<decl.function.free/>',
            '<decl.function.returntype><ref.class>MissingID</ref.class></decl.function.returntype>',
            '<root><decl.function.returntype/><decl.function.returntype/></root>',
        ]:
            with self.subTest(declaration=declaration):
                self.assertIsNone(self.parser.parse(declaration))
