"""
solid-name: KahnCycleDetector
solid-category: service
solid-spec: [SPEC-027]
solid-description: Determines whether a directed graph contains a cycle.
"""

from __future__ import annotations

from typing import Protocol


class CycleDetecting(Protocol):

    def has_cycle(self, adjacency: dict[str, list[str]], in_degree: dict[str, int]) -> bool: ...


class KahnCycleDetector:

    def has_cycle(self, adjacency: dict[str, list[str]], in_degree: dict[str, int]) -> bool:
        in_degree = dict(in_degree)
        queue = [node for node, deg in in_degree.items() if deg == 0]
        visited = 0
        while queue:
            node = queue.pop(0)
            visited += 1
            for neighbor in adjacency[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return visited != len(in_degree)