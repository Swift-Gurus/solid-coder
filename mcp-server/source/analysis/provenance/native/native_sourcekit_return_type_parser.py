"""Resolves call-site return contracts using compiler-authored symbol references."""

from contextlib import ExitStack
from subprocess import SubprocessError
from typing import ContextManager

from harness.flow_validation_error import FlowValidationError
from source.analysis.provenance.native.native_sourcekit_cursor_info import NativeSourceKitCursorInfo
from source.analysis.provenance.native.source_call_reference import SourceCallReference
from source.analysis.provenance.source_symbol_provenance import SourceSymbolResolution
from source.analysis.provenance.source_unresolved_symbol import SourceUnresolvedSymbol
from source.analysis.provenance.sourcekit_symbol import SourceKitSymbol
from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing


"""
solid-name: NativeSourceKitReturnTypeParser
solid-category: boundary-adapter
solid-spec: [SPEC-064]
solid-description: Resolves method-result contracts in one lazy document session, verifies callee and returned-type identities, and preserves unavailable provider evidence.
"""
class NativeSourceKitReturnTypeParser(SourceSyntaxParsing[SourceCallReference, SourceSymbolResolution]):
    def __init__(
        self,
        session: ContextManager[SourceSyntaxParsing[int | str, NativeSourceKitCursorInfo]],
        scope: ExitStack,
        references: SourceSyntaxParsing[str, str | None],
        symbols: SourceSyntaxParsing[list[SourceKitSymbol], SourceSymbolResolution],
    ) -> None:
        self._session = session
        self._scope = scope
        self._references = references
        self._symbols = symbols
        self._document: SourceSyntaxParsing[int | str, NativeSourceKitCursorInfo] | None = None
        self._failure: str | None = None

    def parse(self, source: SourceCallReference) -> SourceSymbolResolution:
        if self._failure is not None:
            return SourceUnresolvedSymbol(reason=self._failure)
        try:
            if self._document is None:
                self._document = self._scope.enter_context(self._session)
            callee = self._document.parse(source.offset)
            if callee.symbol_id != source.symbol_id:
                return SourceUnresolvedSymbol(reason="The native service did not confirm the exact inspected callee identity.")
            reference = self._references.parse(callee.annotated_declaration)
            if reference is None:
                return SourceUnresolvedSymbol(reason="The compiler did not supply one supported semantic return-type reference.")
            result = self._document.parse(reference)
            if result.symbol_id != reference:
                return SourceUnresolvedSymbol(reason="The native service did not resolve the requested return-type identity.")
            return self._symbols.parse([result])
        except (OSError, ValueError, SubprocessError, FlowValidationError) as error:
            self._failure = f"Method return-type resolution is unavailable: {error}"
            return SourceUnresolvedSymbol(reason=self._failure)
