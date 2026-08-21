"""Resolves deterministic tags applicable to one analyzed source unit."""

from source.source_unit_tags_resolving import SourceUnitTagsResolving
from source.technology_detection import TechnologyDetection
from source.technology_detection_scope_matching import (
    TechnologyDetectionScopeMatching,
)


"""
solid-name: SourceUnitTagsResolver
solid-category: service
solid-spec: [SPEC-040]
solid-description: Selects inherited and unit-specific technology tags for a stable analyzed unit identity.
"""
class SourceUnitTagsResolver(SourceUnitTagsResolving):
    def __init__(
        self,
        inherited_scope: TechnologyDetectionScopeMatching,
    ) -> None:
        self._inherited_scope = inherited_scope

    def resolve(
        self,
        detections: list[TechnologyDetection],
        unit_identity: str,
    ) -> list[str]:
        return [
            detection.tag
            for detection in detections
            if self._inherited_scope.matches(detection)
            or detection.scope_identity == unit_identity
        ]
