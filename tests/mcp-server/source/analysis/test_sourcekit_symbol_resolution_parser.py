"""Prevents semantic omissions from becoming ownership proof."""

from pathlib import Path
from unittest import TestCase

from source.analysis.provenance.file_uri_path_parser import FileUriPathParser
from source.analysis.provenance.semantic_symbol_kind import SemanticSymbolKind
from source.analysis.provenance.sourcekit_symbol import SourceKitSymbol
from source.analysis.provenance.sourcekit_symbol_resolution_parser import (
    SourceKitSymbolResolutionParser,
)


class TestSourceKitSymbolResolutionParser(TestCase):
    def setUp(self):
        self.parser = SourceKitSymbolResolutionParser(
            allowed_kinds=frozenset(
                {SemanticSymbolKind.INTERFACE, SemanticSymbolKind.CLASS}
            ),
            paths=FileUriPathParser(),
        )

    def test_sdk_proof_does_not_require_local_source(self):
        result = self.parser.parse(
            [SourceKitSymbol(symbol_id="sdk", kind=5, is_system=True)]
        )
        self.assertEqual(result.kind, "sdk")

    def test_declaration_paths_decode_spaces(self):
        result = self.parser.parse(
            [
                SourceKitSymbol(
                    symbol_id="owned",
                    kind=11,
                    declaration_uri="file:///project/My%20Interface.swift",
                )
            ]
        )
        self.assertEqual(result.declaration_path, Path("/project/My Interface.swift"))

    def test_missing_or_ambiguous_symbols_preserve_uncertainty(self):
        self.assertEqual(self.parser.parse([]).kind, "unresolved")
        self.assertEqual(
            self.parser.parse([SourceKitSymbol(), SourceKitSymbol()]).kind, "ambiguous"
        )

    def test_alias_without_type_category_is_not_a_verified_contract(self):
        result = self.parser.parse(
            [
                SourceKitSymbol(
                    symbol_id="alias", declaration_uri="file:///project/Alias.swift"
                )
            ]
        )
        self.assertEqual(result.kind, "unresolved")

    def test_variable_is_not_a_type(self):
        self.assertEqual(
            self.parser.parse([SourceKitSymbol(symbol_id="parameter", kind=13)]).kind,
            "unresolved",
        )

    def test_module_name_alone_does_not_establish_external_ownership(self):
        result = self.parser.parse(
            [
                SourceKitSymbol(
                    symbol_id="module-member", kind=5, module_name="Framework"
                )
            ]
        )
        self.assertEqual(result.kind, "unresolved")

    def test_generated_interface_is_not_the_original_declaration(self):
        result = self.parser.parse(
            [
                SourceKitSymbol(
                    symbol_id="generated",
                    kind=11,
                    declaration_uri="file:///tmp/Generated.swiftinterface",
                )
            ]
        )
        self.assertEqual(result.kind, "unresolved")

    def test_remote_uri_is_not_a_local_declaration(self):
        result = self.parser.parse(
            [
                SourceKitSymbol(
                    symbol_id="remote",
                    kind=11,
                    declaration_uri="file://remote/path.swift",
                )
            ]
        )
        self.assertEqual(result.kind, "unresolved")
