"""Defines incoming-edge checks for typed directed graphs."""

from typing import Protocol

from harness.directed_graph import DirectedGraph


"""
solid-name: IncomingEdgeChecking
solid-category: abstraction
solid-spec: [SPEC-027]
solid-description: Contract for detecting an incoming edge from a selected set of graph nodes.
"""
class IncomingEdgeChecking(Protocol):

    def has_incoming_edge(
        self,
        node_id: str,
        source_ids: list[str],
        graph: DirectedGraph,
    ) -> bool: ...
