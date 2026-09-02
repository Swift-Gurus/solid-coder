"""Defines selection of authored step templates owned by an include group."""

from typing import Protocol

from harness.include_alias_group import IncludeAliasGroup
from harness.models import FlowDef, StepDef


"""
solid-name: IncludeGroupTemplatesSelecting
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for selecting the authored workflow-step templates owned by an include group.
"""
class IncludeGroupTemplatesSelecting(Protocol):
    def select(
        self,
        flow: FlowDef,
        group: IncludeAliasGroup,
    ) -> list[StepDef]: ...
