"""Creates auditable Swift file-tag detections from matched source signals."""

from source.resolved_analysis_source import ResolvedAnalysisSource
from source.source_evidence_resolving import SourceEvidenceResolving
from source.swift_file_tag_detection_creating import SwiftFileTagDetectionCreating
from source.technology_detection import TechnologyDetection
from source.technology_detection_scope import TechnologyDetectionScope


"""
solid-name: SwiftFileTagDetectionCreator
solid-category: service
solid-spec: [SPEC-039, SPEC-040]
solid-description: Produces auditable Swift technology-tag detections with precise source evidence.
"""
class SwiftFileTagDetectionCreator(SwiftFileTagDetectionCreating):
    def __init__(self, evidence_resolver: SourceEvidenceResolving) -> None:
        self._evidence_resolver = evidence_resolver

    def create(
        self,
        tag: str,
        signal: str,
        source: ResolvedAnalysisSource,
    ) -> TechnologyDetection:
        start_offset = source.text.casefold().find(signal.casefold())
        bounded_start = max(start_offset, 0)
        return TechnologyDetection(
            tag=tag,
            detector_identity="swift-syntax-tags-v1",
            scope=TechnologyDetectionScope.FILE,
            scope_identity=source.identity,
            evidence=[
                self._evidence_resolver.resolve(
                    fact=f"Swift syntax signal {signal}",
                    source=source.text,
                    start_offset=bounded_start,
                    end_offset=bounded_start + len(signal),
                )
            ],
        )
