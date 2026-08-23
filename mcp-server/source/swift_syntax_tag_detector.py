"""Detects applicable tags from Swift syntax signals."""

from source.resolved_analysis_source import ResolvedAnalysisSource
from source.source_unit import SourceUnit
from source.swift_file_tag_detection_creating import SwiftFileTagDetectionCreating
from source.swift_syntax_registration_matching import SwiftSyntaxRegistrationMatching
from source.swift_syntax_tag_registration import SwiftSyntaxTagRegistration
from source.technology_detection import TechnologyDetection


"""
solid-name: SwiftSyntaxTagDetector
solid-category: service
solid-spec: [SPEC-039, SPEC-040]
solid-description: Detects applicable technology tags in Swift source files and records auditable evidence for each detection.
"""
class SwiftSyntaxTagDetector:
    def __init__(
        self,
        matcher: SwiftSyntaxRegistrationMatching,
        detection_creator: SwiftFileTagDetectionCreating,
        registrations: list[SwiftSyntaxTagRegistration],
    ) -> None:
        self._matcher = matcher
        self._detection_creator = detection_creator
        self._registrations = registrations

    def detect(
        self,
        parser_document: str,
        source: ResolvedAnalysisSource,
        units: list[SourceUnit],
    ) -> list[TechnologyDetection]:
        detections: list[TechnologyDetection] = []
        for registration in self._registrations:
            signal = self._matcher.match(parser_document, registration)
            if signal is None:
                continue
            detections.extend(
                self._detection_creator.create(tag, signal, source)
                for tag in registration.tags
            )
        return detections
