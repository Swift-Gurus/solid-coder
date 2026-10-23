"""Stores the complete deterministic component reduction audit."""

from harness.component_metrics.indexed_relation_edge import IndexedRelationEdge
from harness.component_metrics.pairwise_projection_evidence import (
    PairwiseProjectionEvidence,
)
from pydantic import BaseModel, ConfigDict

"""
solid-name: ComponentMetricEvidence
solid-category: model
solid-spec: [SPEC-059]
solid-description: Preserves projected sets, matched pairs, and connected groups for auditing component-derived metrics.
"""


class ComponentMetricEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    projections: list[PairwiseProjectionEvidence]
    edges: list[IndexedRelationEdge]
    components: list[list[int]]
