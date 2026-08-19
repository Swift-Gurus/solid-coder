"""Detects unit-scoped Swift view tags."""

from findings.review_unit_kind import ReviewUnitKind
from source.resolved_analysis_source import ResolvedAnalysisSource
from source.source_evidence_resolving import SourceEvidenceResolving
from source.source_unit import SourceUnit
from source.swift_ast_items_loading import SwiftASTItemsLoading
from source.swift_view_declaration_qualifying import SwiftViewDeclarationQualifying
from source.technology_detection import TechnologyDetection
from source.technology_detection_scope import TechnologyDetectionScope


"""
solid-name: SwiftViewTagDetector
solid-category: boundary-adapter
solid-spec: [SPEC-040]
solid-description: Determines auditable view tags from structured Swift declaration traits.
"""
class SwiftViewTagDetector:

    def __init__(
        self,
        items_loader: SwiftASTItemsLoading,
        declaration_qualifier: SwiftViewDeclarationQualifying,
        evidence_resolver: SourceEvidenceResolving,
    ) -> None:
        self._items_loader = items_loader
        self._declaration_qualifier = declaration_qualifier
        self._evidence_resolver = evidence_resolver

    def detect(
        self,
        parser_document: str,
        source: ResolvedAnalysisSource,
        units: list[SourceUnit],
    ) -> list[TechnologyDetection]:
        detections: list[TechnologyDetection] = []
        for item in self._items_loader.load(parser_document):
            if not self._declaration_qualifier.qualifies(item):
                continue
            source_range = item.get("range") if isinstance(item, dict) else None
            if not isinstance(source_range, dict):
                continue
            start_offset = source_range.get("start")
            if not isinstance(start_offset, int):
                continue
            unit = next(
                (
                    candidate
                    for candidate in units
                    if candidate.kind is ReviewUnitKind.STRUCT
                    and candidate.start_offset == start_offset
                ),
                None,
            )
            if unit is None:
                continue
            detections.append(
                TechnologyDetection(
                    tag="view",
                    detector_identity="swift-view-traits-v1",
                    scope=TechnologyDetectionScope.UNIT,
                    scope_identity=unit.identity,
                    evidence=[
                        self._evidence_resolver.resolve(
                            fact=f"struct {unit.name} declares body",
                            source=source.text,
                            start_offset=unit.start_offset,
                            end_offset=unit.end_offset,
                        )
                    ],
                )
            )
        return detections
