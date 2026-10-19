"""Derives recoverable diagnostics from substitutable syntax error evidence."""

from source.analysis.syntax_diagnostic_node_reading import SyntaxDiagnosticNodeReading
from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing
from source.source_parse_diagnostic import SourceParseDiagnostic


"""
solid-name: SwiftSyntaxDiagnosticParser
solid-category: service
solid-spec: [SPEC-063]
solid-description: Reports missing or unrecognized Swift syntax with source-line evidence, including incomplete types with hidden missing tokens.
"""
class SwiftSyntaxDiagnosticParser(SourceSyntaxParsing[SyntaxDiagnosticNodeReading, SourceParseDiagnostic | None]):
    def parse(self, source: SyntaxDiagnosticNodeReading) -> SourceParseDiagnostic | None:
        if not (source.is_error or source.is_missing or (source.has_error and source.child_count == 0)):
            return None
        return SourceParseDiagnostic(
            code="swift.partial_parse",
            message=(
                f"Missing syntax token: {source.type}"
                if source.is_missing else "Unrecognized Swift syntax"
            ),
            line=source.start_point.row + 1,
        )
