"""Defines matching of technology detections to one configured scope."""

from typing import Protocol

from source.technology_detection import TechnologyDetection


"""
solid-name: TechnologyDetectionScopeMatching
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for recognizing technology detections belonging to one configured scope policy.
"""
class TechnologyDetectionScopeMatching(Protocol):
    def matches(self, detection: TechnologyDetection) -> bool: ...
