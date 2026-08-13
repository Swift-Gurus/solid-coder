"""Validates workflow include cycles."""

from harness.cycle_detecting import CycleDetecting
from harness.directed_graph_creating import DirectedGraphCreating
from harness.directed_graph_edge import DirectedGraphEdge
from harness.flow_validation_error_creating import FlowValidationErrorCreating


"""
solid-name: IncludeCycleValidator
solid-category: service
solid-spec: [SPEC-027, SPEC-035]
solid-description: Rejects cyclic workflow include chains.
"""
class IncludeCycleValidator:

    def __init__(
        self,
        graph_factory: DirectedGraphCreating,
        cycle_detector: CycleDetecting,
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._graph_factory = graph_factory
        self._cycle_detector = cycle_detector
        self._error_factory = error_factory

    def validate(self, include_chain: list[str]) -> None:
        if len(include_chain) < 2:
            return
        node_ids: list[str] = []
        for identifier in include_chain:
            if identifier not in node_ids:
                node_ids.append(identifier)
        edges = [
            DirectedGraphEdge(
                source_id=include_chain[index],
                target_id=include_chain[index + 1],
            )
            for index in range(len(include_chain) - 1)
        ]
        graph = self._graph_factory.create(node_ids, edges)
        if self._cycle_detector.has_cycle(graph):
            raise self._error_factory.create(
                f"Circular include detected: {' -> '.join(include_chain)}"
            )
