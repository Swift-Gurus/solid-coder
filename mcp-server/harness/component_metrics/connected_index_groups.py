"""Partitions indexed nodes through undirected edges."""

from typing import Protocol

from harness.component_metrics.indexed_relation_edge import IndexedRelationEdge

"""
solid-name: IndexComponentsResolving
solid-category: abstraction
solid-spec: [SPEC-059]
solid-description: Contract for partitioning indexed nodes into stable connected components.
"""


class IndexComponentsResolving(Protocol):
    def resolve(
        self, indexes: list[int], edges: list[IndexedRelationEdge]
    ) -> list[list[int]]: ...


"""
solid-name: ConnectedIndexGroups
solid-category: utility
solid-spec: [SPEC-059]
solid-description: Computes transitive undirected components while retaining isolated nodes and stable source ordering.
"""


class ConnectedIndexGroups(IndexComponentsResolving):
    def resolve(
        self, indexes: list[int], edges: list[IndexedRelationEdge]
    ) -> list[list[int]]:
        groups = [{index} for index in indexes]
        for edge in edges:
            connected = [
                group
                for group in groups
                if edge.left_index in group or edge.right_index in group
            ]
            if not connected:
                continue
            merged: set[int] = set()
            for group in connected:
                merged.update(group)
                groups.remove(group)
            groups.append(merged)
        return sorted((sorted(group) for group in groups), key=lambda group: group[0])
