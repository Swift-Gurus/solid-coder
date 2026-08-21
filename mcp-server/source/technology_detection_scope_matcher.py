"""Matches technology detections to one configured scope."""

from source.technology_detection import TechnologyDetection
from source.technology_detection_scope import TechnologyDetectionScope
from source.technology_detection_scope_matching import (
    TechnologyDetectionScopeMatching,
)


"""
solid-name: TechnologyDetectionScopeMatcher
solid-category: service
solid-spec: [SPEC-040]
solid-description: Recognizes technology detections whose typed scope equals an injected scope selection.
"""
class TechnologyDetectionScopeMatcher(TechnologyDetectionScopeMatching):
    def __init__(self, scope: TechnologyDetectionScope) -> None:
        self._scope = scope

    def matches(self, detection: TechnologyDetection) -> bool:
        return detection.scope is self._scope
