"""Detects unit-scoped Swift view tags."""

from findings.review_unit_kind import ReviewUnitKind
from source.analysis.source_syntax_inventory import SourceSyntaxInventory
from source.members.source_member_kind import SourceMemberKind
from source.resolved_analysis_source import ResolvedAnalysisSource
from source.source_evidence import SourceEvidence
from source.swift_tag_detector import SwiftTagDetecting
from source.technology_detection import TechnologyDetection
from source.technology_detection_scope import TechnologyDetectionScope


"""
solid-name: SwiftViewTagDetector
solid-category: boundary-adapter
solid-spec: [SPEC-040]
solid-description: Determines auditable view tags from structured Swift declaration traits.
"""
class SwiftViewTagDetector(SwiftTagDetecting):

    def detect(
        self,
        inventory: SourceSyntaxInventory,
        source: ResolvedAnalysisSource,
    ) -> list[TechnologyDetection]:
        detections: list[TechnologyDetection] = []
        for unit in inventory.units:
            if unit.kind is not ReviewUnitKind.STRUCT or not any(
                member.kind is SourceMemberKind.PROPERTY and member.name == "body"
                for member in unit.members
            ):
                continue
            detections.append(
                TechnologyDetection(
                    tag="view",
                    detector_identity="swift-view-traits-v1",
                    scope=TechnologyDetectionScope.UNIT,
                    scope_identity=unit.identity,
                    evidence=[
                        SourceEvidence(
                            fact=f"struct {unit.name} declares body",
                            span=unit.span,
                        )
                    ],
                )
            )
        return detections
