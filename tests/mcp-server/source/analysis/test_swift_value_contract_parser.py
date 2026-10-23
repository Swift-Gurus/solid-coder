"""Checks type lookup from verified value bindings."""

from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock

import tree_sitter_swift
from source.analysis.provenance.file_uri_path_parser import FileUriPathParser
from source.analysis.provenance.semantic_symbol_kind import SemanticSymbolKind
from source.analysis.provenance.sourcekit_document import SemanticSymbolLookingUp
from source.analysis.provenance.sourcekit_symbol import SourceKitSymbol
from source.analysis.provenance.sourcekit_symbol_resolution_parser import (
    SourceKitSymbolResolutionParser,
)
from source.analysis.provenance.swift_binding_annotation_parser import (
    SwiftBindingAnnotationParser,
)
from source.analysis.provenance.swift_type_reference_position_parser import (
    SwiftTypeReferencePositionParser,
)
from source.analysis.provenance.swift_value_contract_parser import (
    SwiftValueContractParser,
)
from source.analysis.provenance.utf8_semantic_offset_resolver import (
    UTF8SemanticOffsetResolver,
)
from source.analysis.provenance.utf16_source_position_resolver import (
    UTF16SourcePositionResolver,
)
from source.analysis.tree_sitter_nodes_parser import TreeSitterNodesParser
from source.repository_source_snapshot import RepositorySourceSnapshot
from tree_sitter import Language, Parser


class TestSwiftValueContractParser(TestCase):
    def setUp(self):
        self.path = Path("/project/Unwritten.swift")
        self.source = "protocol Service {}\nfunc inspect(_ value: any Service) {}"
        self.document = Mock(spec=SemanticSymbolLookingUp)
        self.document.lookup.return_value = [
            SourceKitSymbol(
                symbol_id="service-type",
                kind=11,
                declaration_uri=self.path.as_uri(),
            )
        ]
        self.value = SourceKitSymbol(
            symbol_id="parameter",
            kind=13,
            declaration_uri=self.path.as_uri(),
            declaration_position=UTF16SourcePositionResolver().resolve(
                self.source, self.source.encode().index(b"value")
            ),
        )
        self.parser = SwiftValueContractParser(
            source=RepositorySourceSnapshot(
                path=self.path,
                source_identity=str(self.path),
                content=self.source,
                content_sha256="fixture",
            ),
            annotations=SwiftBindingAnnotationParser(
                Parser(Language(tree_sitter_swift.language())).parse(
                    self.source.encode()
                )
            ),
            document=self.document,
            paths=FileUriPathParser(),
            offsets=UTF8SemanticOffsetResolver(),
            positions=SwiftTypeReferencePositionParser(
                TreeSitterNodesParser(frozenset(), frozenset())
            ),
            types=SourceKitSymbolResolutionParser(
                frozenset({SemanticSymbolKind.INTERFACE, SemanticSymbolKind.CLASS}),
                FileUriPathParser(),
            ),
        )

    def test_resolves_type_not_parameter_identity(self):
        result = self.parser.parse([self.value])
        self.assertEqual(result.symbol_id, "service-type")
        self.document.lookup.assert_called_once_with(
            self.source.encode().rindex(b"Service")
        )

    def test_preserves_sdk_proof(self):
        self.document.lookup.return_value = [
            SourceKitSymbol(symbol_id="sdk-type", kind=5, is_system=True)
        ]
        self.assertEqual(self.parser.parse([self.value]).kind, "sdk")

    def test_non_value_symbol_is_not_used_as_a_binding(self):
        self.assertEqual(
            self.parser.parse([SourceKitSymbol(symbol_id="function", kind=12)]).kind,
            "unresolved",
        )
        self.document.lookup.assert_not_called()

    def test_binding_in_another_document_is_not_textually_guessed(self):
        foreign = SourceKitSymbol(
            symbol_id="other",
            kind=13,
            declaration_uri="file:///other.swift",
            declaration_position=self.value.declaration_position,
        )
        self.assertEqual(self.parser.parse([foreign]).kind, "unresolved")
        self.document.lookup.assert_not_called()

    def test_ambiguous_binding_is_preserved(self):
        self.assertEqual(self.parser.parse([self.value, self.value]).kind, "ambiguous")
        self.document.lookup.assert_not_called()

    def test_type_alias_without_semantic_type_category_is_unresolved(self):
        self.document.lookup.return_value = [
            SourceKitSymbol(symbol_id="alias", declaration_uri=self.path.as_uri())
        ]
        self.assertEqual(self.parser.parse([self.value]).kind, "unresolved")
