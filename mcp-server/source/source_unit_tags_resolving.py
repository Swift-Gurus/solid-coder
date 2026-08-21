"""Defines deterministic tag resolution for one analyzed source unit."""

from typing import Protocol

from source.technology_detection import TechnologyDetection


"""
solid-name: SourceUnitTagsResolving
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for selecting normalized technology tags applicable to one analyzed source unit.
"""
class SourceUnitTagsResolving(Protocol):
    def resolve(
        self,
        detections: list[TechnologyDetection],
        unit_identity: str,
    ) -> list[str]: ...
