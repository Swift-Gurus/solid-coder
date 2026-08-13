"""Detects cycles in typed directed graphs."""

from harness.cycle_detecting import CycleDetecting
from harness.directed_graph import DirectedGraph
from harness.incoming_edge_checking import IncomingEdgeChecking


"""
solid-name: KahnCycleDetector
solid-category: service
solid-spec: [SPEC-027]
solid-description: Determines whether a typed directed graph contains a cycle.
"""
class KahnCycleDetector(CycleDetecting):

    def __init__(self, incoming_edge_checker: IncomingEdgeChecking) -> None:
        self._incoming_edge_checker = incoming_edge_checker

    def has_cycle(self, graph: DirectedGraph) -> bool:
        remaining_ids = [node.identifier for node in graph.nodes]
        while remaining_ids:
            removable_id = next(
                (
                    node_id
                    for node_id in remaining_ids
                    if not self._incoming_edge_checker.has_incoming_edge(
                        node_id,
                        remaining_ids,
                        graph,
                    )
                ),
                None,
            )
            if removable_id is None:
                return True
            remaining_ids.remove(removable_id)
        return False
