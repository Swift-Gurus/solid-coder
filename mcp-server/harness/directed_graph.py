"""Defines a directed graph as typed nodes."""

from __future__ import annotations

from dataclasses import dataclass, field

from harness.directed_graph_node import DirectedGraphNode


"""
solid-name: DirectedGraph
solid-category: model
solid-spec: [SPEC-027]
solid-description: Represents a directed graph as an ordered collection of typed nodes.
"""
@dataclass
class DirectedGraph:
    nodes: list[DirectedGraphNode] = field(default_factory=list)

    def find(self, identifier: str) -> DirectedGraphNode | None:
        return next(
            (node for node in self.nodes if node.identifier == identifier),
            None,
        )
