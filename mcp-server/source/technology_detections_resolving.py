"""Defines selection of technology detections by source identity."""

from typing import Protocol

from source.technology_detection import TechnologyDetection


"""
solid-name: TechnologyDetectionsResolving
solid-category: abstraction
solid-spec: [SPEC-040, SPEC-041]
solid-description: Contract for selecting ordered technology evidence belonging to stable source-scope identities.
"""
class TechnologyDetectionsResolving(Protocol):
    def resolve(
        self,
        detections: list[TechnologyDetection],
        scope_identities: list[str],
    ) -> list[TechnologyDetection]: ...
