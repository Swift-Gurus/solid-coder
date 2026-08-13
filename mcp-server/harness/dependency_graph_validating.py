"""Defines workflow dependency-graph validation."""

from __future__ import annotations

from typing import Protocol

from harness.graph_step_field_reading import GraphStepFieldReading
from harness.include_alias_group import IncludeAliasGroup


"""
solid-name: DependencyGraphValidating
solid-category: abstraction
solid-spec: [SPEC-027]
solid-description: Contract for validating workflow-step identities and dependency relationships.
"""
class DependencyGraphValidating(Protocol):
    def validate(
        self,
        steps: list[GraphStepFieldReading],
        alias_groups: list[IncludeAliasGroup] | None = None,
    ) -> None: ...
