"""Defines deterministic tag detection from one Swift parser result."""

from typing import Protocol

from source.resolved_analysis_source import ResolvedAnalysisSource
from source.source_unit import SourceUnit
from source.technology_detection import TechnologyDetection


"""
solid-name: SwiftTagDetecting
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for deriving auditable source tags from structured Swift parser output.
"""
class SwiftTagDetecting(Protocol):

    def detect(
        self,
        parser_document: str,
        source: ResolvedAnalysisSource,
        units: list[SourceUnit],
    ) -> list[TechnologyDetection]: ...
