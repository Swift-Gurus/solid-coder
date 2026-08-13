"""Defines alias qualification of included workflow steps."""

from typing import Protocol


"""
solid-name: StepQualifying
solid-category: abstraction
solid-spec: [SPEC-027, SPEC-035]
solid-description: Contract for qualifying included step IDs and their sibling dependencies under an alias.
"""
class StepQualifying(Protocol):

    def qualify(
        self,
        step: dict,
        alias: str,
        local_dependency_ids: set[str],
    ) -> dict:
        ...
