"""Defines evidence-backed creation of one Swift file-tag detection."""

from typing import Protocol

from source.resolved_analysis_source import ResolvedAnalysisSource
from source.technology_detection import TechnologyDetection


"""
solid-name: SwiftFileTagDetectionCreating
solid-category: abstraction
solid-spec: [SPEC-039, SPEC-040]
solid-description: Contract for producing one auditable Swift file-tag detection from a matched source signal.
"""
class SwiftFileTagDetectionCreating(Protocol):
    def create(
        self,
        tag: str,
        signal: str,
        source: ResolvedAnalysisSource,
    ) -> TechnologyDetection: ...
