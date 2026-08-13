"""Defines one directed graph edge."""

from dataclasses import dataclass


"""
solid-name: DirectedGraphEdge
solid-category: model
solid-spec: [SPEC-027]
solid-description: Represents one directed connection between two graph-node identifiers.
"""
@dataclass(frozen=True)
class DirectedGraphEdge:
    source_id: str
    target_id: str
