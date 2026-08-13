"""Creates typed directed graphs."""

from harness.directed_graph import DirectedGraph
from harness.directed_graph_creating import DirectedGraphCreating
from harness.directed_graph_edge import DirectedGraphEdge
from harness.directed_graph_node import DirectedGraphNode


"""
solid-name: DirectedGraphFactory
solid-category: factory
solid-spec: [SPEC-027]
solid-description: Creates a typed directed graph from node identifiers and edges.
"""
class DirectedGraphFactory(DirectedGraphCreating):

    def create(
        self,
        node_ids: list[str],
        edges: list[DirectedGraphEdge],
    ) -> DirectedGraph:
        graph = DirectedGraph(
            nodes=[DirectedGraphNode(identifier=node_id) for node_id in node_ids]
        )
        for edge in edges:
            source = graph.find(edge.source_id)
            if source is not None:
                source.outgoing_ids.append(edge.target_id)
        return graph
