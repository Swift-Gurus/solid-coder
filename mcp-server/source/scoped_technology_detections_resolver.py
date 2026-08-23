"""Selects ordered technology detections for stable scope identities."""

from source.technology_detection import TechnologyDetection
from source.technology_detections_resolving import (
    TechnologyDetectionsResolving,
)


"""
solid-name: ScopedTechnologyDetectionsResolver
solid-category: service
solid-spec: [SPEC-040, SPEC-041]
solid-description: Retains ordered technology evidence whose recorded scope belongs to an accepted source identity.
"""
class ScopedTechnologyDetectionsResolver(TechnologyDetectionsResolving):
    def resolve(
        self,
        detections: list[TechnologyDetection],
        scope_identities: list[str],
    ) -> list[TechnologyDetection]:
        accepted_identities = set(scope_identities)
        return [
            detection
            for detection in detections
            if detection.scope_identity in accepted_identities
        ]
