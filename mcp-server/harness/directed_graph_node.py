"""Defines one node in a directed graph."""

from dataclasses import dataclass, field


"""
solid-name: DirectedGraphNode
solid-category: model
solid-spec: [SPEC-027]
solid-description: Represents one directed-graph node and its outgoing neighbor identifiers.
"""
@dataclass
class DirectedGraphNode:
    identifier: str
    outgoing_ids: list[str] = field(default_factory=list)
