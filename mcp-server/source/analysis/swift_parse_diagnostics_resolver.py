"""Defines recoverable Swift parse-diagnostic derivation."""

from typing import Protocol

from tree_sitter import Node

from source.source_parse_diagnostic import SourceParseDiagnostic


"""
solid-name: SwiftParseDiagnosticsResolving
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for deriving recoverable diagnostics from parsed Swift source.
"""
class SwiftParseDiagnosticsResolving(Protocol):
    def resolve(self, source: Node) -> list[SourceParseDiagnostic]: ...


"""
solid-name: SwiftParseDiagnosticsResolver
solid-category: boundary-adapter
solid-spec: [SPEC-040, SPEC-057]
solid-description: Derives stable recoverable diagnostics for incomplete Swift source analysis.
"""
class SwiftParseDiagnosticsResolver(SwiftParseDiagnosticsResolving):
    def resolve(self, source: Node) -> list[SourceParseDiagnostic]:
        diagnostics: list[SourceParseDiagnostic] = []
        pending = [source]
        while pending:
            node = pending.pop()
            if node.is_error or node.is_missing:
                diagnostics.append(SourceParseDiagnostic(
                    code="swift.partial_parse",
                    message=(
                        f"Missing syntax token: {node.type}"
                        if node.is_missing else "Unrecognized Swift syntax"
                    ),
                    line=node.start_point.row + 1,
                ))
            if node.has_error:
                pending.extend(reversed(node.children))
        return diagnostics
