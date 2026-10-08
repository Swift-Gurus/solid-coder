from tree_sitter import Node

from source.analysis.signatures.source_callable_signature import SourceCallableSignature
from source.analysis.signatures.source_subscript_signature import SourceSubscriptSignature
from source.analysis.signatures.source_unresolved_signature import SourceUnresolvedSignature
from source.analysis.signatures.swift_member_syntax import SwiftMemberSyntax
from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing


"""
solid-name: TreeSitterSwiftSubscriptSignatureParser
solid-category: boundary-adapter
solid-spec: [SPEC-057]
solid-description: Derives complete subscript signature facts while safely reporting incomplete or unsupported declarations.
"""
class TreeSitterSwiftSubscriptSignatureParser(SourceSyntaxParsing[SwiftMemberSyntax, SourceSubscriptSignature | SourceUnresolvedSignature]):
    def __init__(
        self,
        callables: SourceSyntaxParsing[SwiftMemberSyntax, SourceCallableSignature],
        accessors: SourceSyntaxParsing[Node, list[str]],
    ) -> None:
        self._callables = callables
        self._accessors = accessors

    def parse(self, source: SwiftMemberSyntax) -> SourceSubscriptSignature | SourceUnresolvedSignature:
        accessors = self._accessors.parse(source.declaration)
        if not accessors:
            return SourceUnresolvedSignature(reason="Subscript accessor syntax is unavailable or unsupported")
        callable_signature = self._callables.parse(source)
        if not callable_signature.return_type:
            return SourceUnresolvedSignature(reason="Subscript result type syntax is unavailable or unsupported")
        return SourceSubscriptSignature(callable=callable_signature, accessors=accessors)
