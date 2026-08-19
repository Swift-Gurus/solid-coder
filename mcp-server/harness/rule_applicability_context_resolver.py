"""Resolves rule-applicability context from deterministic source analysis."""

from harness.ordered_string_collecting import OrderedStringCollecting
from harness.rule_applicability_context import RuleApplicabilityContext
from source.source_analysis import SourceAnalysis
from source.source_unit import SourceUnit
from source.technology_detection_scope import TechnologyDetectionScope


"""
solid-name: RuleApplicabilityContextResolver
solid-category: service
solid-spec: [SPEC-039, SPEC-040]
solid-description: Resolves exact extension, unit kind, and inherited deterministic tags for one review unit.
"""
class RuleApplicabilityContextResolver:

    def __init__(self, tag_collector: OrderedStringCollecting) -> None:
        self._tag_collector = tag_collector

    def resolve(
        self,
        analysis: SourceAnalysis,
        unit: SourceUnit,
    ) -> RuleApplicabilityContext:
        file_tags = [
            detection.tag
            for detection in analysis.detections
            if detection.scope is TechnologyDetectionScope.FILE
            and detection.scope_identity == analysis.source_identity
        ]
        unit_tags = [
            detection.tag
            for detection in analysis.detections
            if detection.scope is TechnologyDetectionScope.UNIT
            and detection.scope_identity == unit.identity
        ]
        return RuleApplicabilityContext(
            file_extension=analysis.file_extension,
            unit_kind=unit.kind,
            tags=self._tag_collector.collect([file_tags, unit_tags]),
        )
