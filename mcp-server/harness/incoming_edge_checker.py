"""Checks incoming edges in typed directed graphs."""

from harness.directed_graph import DirectedGraph
from harness.incoming_edge_checking import IncomingEdgeChecking


"""
solid-name: IncomingEdgeChecker
solid-category: service
solid-spec: [SPEC-027]
solid-description: Detects an incoming edge from a selected set of graph nodes.
"""
class IncomingEdgeChecker(IncomingEdgeChecking):

    def has_incoming_edge(
        self,
        node_id: str,
        source_ids: list[str],
        graph: DirectedGraph,
    ) -> bool:
        return any(
            source.identifier in source_ids and node_id in source.outgoing_ids
            for source in graph.nodes
        )
