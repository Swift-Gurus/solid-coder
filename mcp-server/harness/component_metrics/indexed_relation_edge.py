"""Stores one undirected match between source collection indexes."""

from pydantic import BaseModel, ConfigDict


"""
solid-name: IndexedRelationEdge
solid-category: model
solid-spec: [SPEC-059]
solid-description: Identifies a matching pair of collection nodes by their original source indexes.
"""
class IndexedRelationEdge(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    left_index: int
    right_index: int
