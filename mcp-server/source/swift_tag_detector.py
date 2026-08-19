"""Aggregates deterministic Swift tag detectors."""

from source.resolved_analysis_source import ResolvedAnalysisSource
from source.source_unit import SourceUnit
from source.swift_tag_detecting import SwiftTagDetecting
from source.technology_detection import TechnologyDetection


"""
solid-name: SwiftTagDetector
solid-category: service
solid-spec: [SPEC-040]
solid-description: Aggregates ordered auditable tag detections from registered Swift detection capabilities.
"""
class SwiftTagDetector:

    def __init__(self, detectors: list[SwiftTagDetecting]) -> None:
        self._detectors = detectors

    def detect(
        self,
        parser_document: str,
        source: ResolvedAnalysisSource,
        units: list[SourceUnit],
    ) -> list[TechnologyDetection]:
        detections: list[TechnologyDetection] = []
        for detector in self._detectors:
            detections.extend(
                detector.detect(parser_document, source, units)
            )
        return detections
