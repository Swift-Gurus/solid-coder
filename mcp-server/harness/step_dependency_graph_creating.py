"""Defines creation of workflow-step dependency graphs."""

from typing import Protocol

from harness.directed_graph import DirectedGraph
from harness.graph_step_field_reading import GraphStepFieldReading
from harness.include_alias_group import IncludeAliasGroup


"""
solid-name: StepDependencyGraphCreating
solid-category: abstraction
solid-spec: [SPEC-027]
solid-description: Contract for creating a typed dependency graph from workflow steps and include groups.
"""
class StepDependencyGraphCreating(Protocol):

    def create(
        self,
        steps: list[GraphStepFieldReading],
        alias_groups: list[IncludeAliasGroup],
    ) -> DirectedGraph: ...
