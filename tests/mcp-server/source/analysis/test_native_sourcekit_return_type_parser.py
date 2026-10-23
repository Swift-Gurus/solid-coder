"""Checks call-site identity and return-contract evidence independently."""

from contextlib import ExitStack
from unittest import TestCase
from unittest.mock import MagicMock, Mock

from source.analysis.provenance.file_uri_path_parser import FileUriPathParser
from source.analysis.provenance.native.native_sourcekit_cursor_info import (
    NativeSourceKitCursorInfo,
)
from source.analysis.provenance.native.native_sourcekit_return_type_parser import (
    NativeSourceKitReturnTypeParser,
)
from source.analysis.provenance.native.source_call_reference import SourceCallReference
from source.analysis.provenance.native.swift_return_type_reference_parser import (
    SwiftReturnTypeReferenceParser,
)
from source.analysis.provenance.sourcekit_symbol_resolution_parser import (
    SourceKitSymbolResolutionParser,
)
from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing


class TestNativeSourceKitReturnTypeParser(TestCase):
    def setUp(self):
        self.scope = ExitStack()
        self.addCleanup(self.scope.close)
        self.document = Mock(spec=SourceSyntaxParsing)
        self.session = MagicMock()
        self.session.__enter__.return_value = self.document
        self.parser = NativeSourceKitReturnTypeParser(
            self.session,
            self.scope,
            SwiftReturnTypeReferenceParser(),
            SourceKitSymbolResolutionParser(frozenset(), FileUriPathParser()),
        )
        self.call = NativeSourceKitCursorInfo(
            symbol_id="method",
            is_system=True,
            annotated_declaration="<decl.function.free><decl.function.returntype>"
            '<ref.protocol usr="result">Service</ref.protocol>'
            "</decl.function.returntype></decl.function.free>",
        )
        self.reference = SourceCallReference(offset=42, symbol_id="method")

    def test_sdk_method_does_not_make_its_project_owned_result_external(self):
        result = NativeSourceKitCursorInfo.model_validate(
            {"key.usr": "result", "key.filepath": "/project/Service.swift"}
        )
        self.document.parse.side_effect = [self.call, result]
        resolved = self.parser.parse(self.reference)
        self.assertEqual(resolved.kind, "declaration")
        self.assertEqual(resolved.symbol_id, "result")
        self.assertEqual(str(resolved.declaration_path), "/project/Service.swift")

    def test_sdk_return_contract_uses_its_own_provider_evidence(self):
        self.document.parse.side_effect = [
            self.call,
            NativeSourceKitCursorInfo(symbol_id="result", is_system=True),
        ]
        self.assertEqual(self.parser.parse(self.reference).kind, "sdk")

    def test_different_callee_identity_is_not_accepted(self):
        self.document.parse.return_value = self.call
        result = self.parser.parse(
            SourceCallReference(offset=42, symbol_id="different-overload")
        )
        self.assertEqual(result.kind, "unresolved")
        self.document.parse.assert_called_once_with(42)

    def test_different_return_identity_is_not_accepted(self):
        self.document.parse.side_effect = [
            self.call,
            NativeSourceKitCursorInfo(symbol_id="other", is_system=True),
        ]
        self.assertEqual(self.parser.parse(self.reference).kind, "unresolved")

    def test_one_session_serves_multiple_queries(self):
        result = NativeSourceKitCursorInfo(symbol_id="result", is_system=True)
        self.document.parse.side_effect = [self.call, result, self.call, result]
        self.parser.parse(self.reference)
        self.parser.parse(self.reference)
        self.session.__enter__.assert_called_once()

    def test_provider_failure_is_explicit_and_not_retried_on_the_broken_session(self):
        self.document.parse.side_effect = TimeoutError("deadline")
        self.assertIn("deadline", self.parser.parse(self.reference).reason)
        self.assertIn("deadline", self.parser.parse(self.reference).reason)
        self.document.parse.assert_called_once()
