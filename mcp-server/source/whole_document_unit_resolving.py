"""Defines whole-document source-unit resolution."""

from typing import Protocol

from source.resolved_analysis_source import ResolvedAnalysisSource
from source.source_unit import SourceUnit


"""
solid-name: WholeDocumentUnitResolving
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for representing readable source content as one deterministic document unit.
"""
class WholeDocumentUnitResolving(Protocol):

    def resolve(self, source: ResolvedAnalysisSource) -> SourceUnit: ...
