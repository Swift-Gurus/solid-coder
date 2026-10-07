"""Defines deterministic tag detection from one Swift parser result."""

from typing import Protocol

from source.resolved_analysis_source import ResolvedAnalysisSource
from source.analysis.source_syntax_inventory import SourceSyntaxInventory
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
        inventory: SourceSyntaxInventory,
        source: ResolvedAnalysisSource,
    ) -> list[TechnologyDetection]: ...


"""
solid-name: SwiftTagDetector
solid-category: service
solid-spec: [SPEC-040, SPEC-057]
solid-description: Aggregates ordered auditable technology detections for Swift source.
"""
class SwiftTagDetector(SwiftTagDetecting):
    def __init__(self, detectors: list[SwiftTagDetecting]) -> None:
        self._detectors = detectors

    def detect(
        self, inventory: SourceSyntaxInventory, source: ResolvedAnalysisSource,
    ) -> list[TechnologyDetection]:
        detections: list[TechnologyDetection] = []
        for detector in self._detectors:
            detections.extend(detector.detect(inventory, source))
        return detections
