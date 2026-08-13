"""Defines cycle detection for typed directed graphs."""

from typing import Protocol

from harness.directed_graph import DirectedGraph


"""
solid-name: CycleDetecting
solid-category: abstraction
solid-spec: [SPEC-027]
solid-description: Contract for determining whether a typed directed graph contains a cycle.
"""
class CycleDetecting(Protocol):

    def has_cycle(self, graph: DirectedGraph) -> bool: ...
