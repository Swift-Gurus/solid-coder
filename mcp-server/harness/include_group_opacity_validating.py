"""Defines validation of include-group dependency opacity."""

from typing import Protocol

from harness.graph_step_field_reading import GraphStepFieldReading
from harness.include_alias_group import IncludeAliasGroup


"""
solid-name: IncludeGroupOpacityValidating
solid-category: abstraction
solid-spec: [SPEC-027, SPEC-035]
solid-description: Contract for rejecting dependencies that cross unrelated include-group boundaries.
"""
class IncludeGroupOpacityValidating(Protocol):

    def validate(
        self,
        steps: list[GraphStepFieldReading],
        alias_groups: list[IncludeAliasGroup],
    ) -> None: ...
