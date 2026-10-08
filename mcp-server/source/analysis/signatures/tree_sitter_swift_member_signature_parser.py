"""Routes declared Swift member kinds to signature extraction."""

from source.analysis.signatures.source_associated_type_signature import SourceAssociatedTypeSignature
from source.analysis.signatures.source_callable_signature import SourceCallableSignature
from source.analysis.signatures.source_subscript_signature import SourceSubscriptSignature
from source.analysis.signatures.source_unresolved_signature import SourceUnresolvedSignature
from source.analysis.signatures.source_value_signature import SourceValueSignature
from source.analysis.signatures.swift_member_syntax import SwiftMemberSyntax
from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing
from source.members.source_member import SourceMemberSignature
from source.members.source_member_kind import SourceMemberKind


"""
solid-name: TreeSitterSwiftMemberSignatureParser
solid-category: boundary-adapter
solid-spec: [SPEC-057]
solid-description: Routes supported member syntax to typed signature extraction and preserves incomplete or unsupported declarations as unresolved facts.
"""
class TreeSitterSwiftMemberSignatureParser(SourceSyntaxParsing[SwiftMemberSyntax, SourceMemberSignature]):
    def __init__(
        self,
        callables: SourceSyntaxParsing[SwiftMemberSyntax, SourceCallableSignature],
        values: SourceSyntaxParsing[SwiftMemberSyntax, SourceValueSignature | SourceUnresolvedSignature],
        associated_types: SourceSyntaxParsing[SwiftMemberSyntax, SourceAssociatedTypeSignature],
        subscripts: SourceSyntaxParsing[SwiftMemberSyntax, SourceSubscriptSignature | SourceUnresolvedSignature],
    ) -> None:
        self._callables = callables
        self._values = values
        self._associated_types = associated_types
        self._subscripts = subscripts

    def parse(self, source: SwiftMemberSyntax) -> SourceMemberSignature:
        if source.declaration.has_error:
            return SourceUnresolvedSignature(reason="Incomplete declaration syntax prevents signature extraction")
        match source.kind:
            case SourceMemberKind.METHOD | SourceMemberKind.INITIALIZER | SourceMemberKind.DEINITIALIZER:
                return self._callables.parse(source)
            case SourceMemberKind.PROPERTY:
                return self._values.parse(source)
            case SourceMemberKind.ASSOCIATED_TYPE:
                return self._associated_types.parse(source)
            case SourceMemberKind.SUBSCRIPT:
                return self._subscripts.parse(source)
            case _:
                return SourceUnresolvedSignature(reason=f"Signature extraction is not supported for {source.kind.value}")
