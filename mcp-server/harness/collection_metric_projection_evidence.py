"""Defines one auditable collection metric projection."""

from dataclasses import dataclass


"""
solid-name: CollectionMetricProjectionEvidence
solid-category: model
solid-spec: [SPEC-054]
solid-description: Associates one projected scalar metric value with its source index.
"""
@dataclass(frozen=True)
class CollectionMetricProjectionEvidence:
    index: int
    value: object
