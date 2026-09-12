"""Builds typed review files from one completed source analysis."""

from findings.review_unit_kind import ReviewUnitKind
from harness.rule_applicability_context import RuleApplicabilityContext
from harness.rule_applicability_context_resolving import (
    RuleApplicabilityContextResolving,
)
from review.normalized_review_file import NormalizedReviewFile
from review.normalized_review_input import NormalizedReviewInput
from review.normalized_review_unit import NormalizedReviewUnit
from source.repository_source_snapshot import RepositorySourceSnapshot
from source.source_analysis import SourceAnalysis
from source.source_search_context import SourceSearchContext
from source.source_search_target import SourceSearchTarget
from source.technology_detections_resolving import (
    TechnologyDetectionsResolving,
)


"""
solid-name: NormalizedReviewFileBuilder
solid-category: service
solid-spec: [SPEC-039, SPEC-041]
solid-description: Builds normalized review input from analyzed targets, applicability, evidence, and an immutable source snapshot.
"""
class NormalizedReviewFileBuilder:
    def __init__(
        self,
        applicability: RuleApplicabilityContextResolving,
        evidence: TechnologyDetectionsResolving,
    ) -> None:
        self._applicability = applicability
        self._evidence = evidence

    def build(
        self,
        analysis: SourceAnalysis,
        file_target: SourceSearchTarget,
        unit_targets: list[SourceSearchTarget],
        snapshots: list[RepositorySourceSnapshot],
    ) -> NormalizedReviewInput:
        file_evidence = self._evidence.resolve(
            analysis.detections,
            [analysis.source_identity],
        )
        units = [
            NormalizedReviewUnit(
                target=target,
                applicability=self._applicability.resolve(analysis, unit),
                tag_evidence=self._evidence.resolve(
                    analysis.detections,
                    [analysis.source_identity, unit.identity],
                ),
            )
            for unit, target in zip(analysis.units, unit_targets)
        ]
        return NormalizedReviewInput(
            review_file=NormalizedReviewFile(
                target=file_target,
                applicability=RuleApplicabilityContext(
                    file_extension=analysis.file_extension,
                    unit_kind=ReviewUnitKind.DOCUMENT,
                    tags=[detection.tag for detection in file_evidence],
                ),
                tag_evidence=file_evidence,
            ),
            units=units,
            source_context=SourceSearchContext(sources=snapshots),
        )
