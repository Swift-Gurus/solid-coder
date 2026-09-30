"""Defines supported pairwise collection relations."""

from enum import Enum


"""
solid-name: PairwiseRelationOperator
solid-category: model
solid-spec: [SPEC-059]
solid-description: Enumerates deterministic relations between projected collection sets.
"""
class PairwiseRelationOperator(str, Enum):
    INTERSECTS = "intersects"
