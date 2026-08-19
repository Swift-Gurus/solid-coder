"""Defines recoverable Swift parse-diagnostic derivation."""

from typing import Optional, Protocol

from source.source_parse_diagnostic import SourceParseDiagnostic
from source.source_unit import SourceUnit


"""
solid-name: SwiftParseDiagnosticsResolving
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for deriving recoverable diagnostics from a Swift parser outcome and identified units.
"""
class SwiftParseDiagnosticsResolving(Protocol):
    def resolve(
        self,
        exit_code: Optional[int],
        stderr: str,
        units: list[SourceUnit],
    ) -> list[SourceParseDiagnostic]: ...
