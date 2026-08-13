"""Defines creation of typed directed graphs."""

from typing import Protocol

from harness.directed_graph import DirectedGraph
from harness.directed_graph_edge import DirectedGraphEdge


"""
solid-name: DirectedGraphCreating
solid-category: abstraction
solid-spec: [SPEC-027]
solid-description: Contract for creating a typed directed graph from node identifiers and edges.
"""
class DirectedGraphCreating(Protocol):

    def create(
        self,
        node_ids: list[str],
        edges: list[DirectedGraphEdge],
    ) -> DirectedGraph: ...
