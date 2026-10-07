"""Detects applicable tags from Swift syntax signals."""

from source.analysis.source_syntax_inventory import SourceSyntaxInventory
from source.resolved_analysis_source import ResolvedAnalysisSource
from source.source_evidence import SourceEvidence
from source.swift_syntax_registration_matcher import SwiftSyntaxRegistrationMatching
from source.swift_syntax_tag_registration import SwiftSyntaxTagRegistration
from source.swift_tag_detector import SwiftTagDetecting
from source.technology_detection import TechnologyDetection
from source.technology_detection_scope import TechnologyDetectionScope


"""
solid-name: SwiftSyntaxTagDetector
solid-category: service
solid-spec: [SPEC-039, SPEC-040]
solid-description: Detects applicable technology tags in Swift source files and records auditable evidence for each detection.
"""
class SwiftSyntaxTagDetector(SwiftTagDetecting):
    def __init__(
        self,
        matcher: SwiftSyntaxRegistrationMatching,
        registrations: list[SwiftSyntaxTagRegistration],
    ) -> None:
        self._matcher = matcher
        self._registrations = registrations

    def detect(
        self,
        inventory: SourceSyntaxInventory,
        source: ResolvedAnalysisSource,
    ) -> list[TechnologyDetection]:
        detections: list[TechnologyDetection] = []
        for registration in self._registrations:
            signal = self._matcher.match(inventory.signals, registration)
            if signal is None:
                continue
            detections.extend(
                TechnologyDetection(
                    tag=tag,
                    detector_identity="swift-syntax-tags-v1",
                    scope=TechnologyDetectionScope.FILE,
                    scope_identity=source.identity,
                    evidence=[SourceEvidence(
                        fact=f"Swift syntax signal {signal.fact}",
                        span=signal.span,
                    )],
                )
                for tag in registration.tags
            )
        return detections
