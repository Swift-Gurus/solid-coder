"""Defines reusable-fragment resolution across workflow step collections."""

from typing import Protocol


"""
solid-name: StepCollectionUsesResolving
solid-category: abstraction
solid-spec: [SPEC-030, SPEC-035]
solid-description: Contract for resolving reusable fragments across a workflow step collection.
"""
class StepCollectionUsesResolving(Protocol):
    def resolve(
        self,
        steps: list[dict],
        flow_path: str,
        search_paths: list[str],
    ) -> list[dict]: ...
