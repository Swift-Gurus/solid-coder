"""Detects file-scoped tags from exact Swift imports."""

from source.analysis.source_syntax_inventory import SourceSyntaxInventory
from source.resolved_analysis_source import ResolvedAnalysisSource
from source.source_evidence import SourceEvidence
from source.swift_import_tag_registration import SwiftImportTagRegistration
from source.swift_tag_detector import SwiftTagDetecting
from source.technology_detection import TechnologyDetection
from source.technology_detection_scope import TechnologyDetectionScope


"""
solid-name: SwiftImportTagDetector
solid-category: boundary-adapter
solid-spec: [SPEC-040]
solid-description: Determines auditable file technology tags from exact Swift imports.
"""
class SwiftImportTagDetector(SwiftTagDetecting):

    def __init__(
        self,
        registrations: list[SwiftImportTagRegistration],
    ) -> None:
        self._registrations = registrations

    def detect(
        self,
        inventory: SourceSyntaxInventory,
        source: ResolvedAnalysisSource,
    ) -> list[TechnologyDetection]:
        detections: list[TechnologyDetection] = []
        for imported in inventory.imports:
            registration = next(
                (
                    candidate
                    for candidate in self._registrations
                    if candidate.module == imported.fact
                ),
                None,
            )
            if registration is None:
                continue
            detections.extend(
                TechnologyDetection(
                    tag=tag,
                    detector_identity="swift-import-tags-v1",
                    scope=TechnologyDetectionScope.FILE,
                    scope_identity=source.identity,
                    evidence=[SourceEvidence(fact=f"import {imported.fact}", span=imported.span)],
                )
                for tag in registration.tags
            )
        return detections
