"""Derives recoverable diagnostics from Swift parser outcomes."""

from typing import Optional

from source.source_parse_diagnostic import SourceParseDiagnostic
from source.source_unit import SourceUnit
from source.swift_parse_diagnostics_resolving import (
    SwiftParseDiagnosticsResolving,
)


"""
solid-name: SwiftParseDiagnosticsResolver
solid-category: service
solid-spec: [SPEC-040]
solid-description: Derives stable recoverable diagnostics for incomplete Swift source analysis.
"""
class SwiftParseDiagnosticsResolver(SwiftParseDiagnosticsResolving):
    def resolve(
        self,
        exit_code: Optional[int],
        stderr: str,
        units: list[SourceUnit],
    ) -> list[SourceParseDiagnostic]:
        if exit_code == 0:
            return []
        line = units[-1].span.start if units else 1
        message_lines = stderr.strip().splitlines()
        return [SourceParseDiagnostic(
            code="swift.partial_parse",
            message=(
                message_lines[0]
                if message_lines
                else "Swift parser reported an incomplete source file"
            ),
            line=line,
        )]
