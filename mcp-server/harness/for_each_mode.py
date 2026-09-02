"""Defines how ready for-each instances are presented to the model."""

from enum import Enum


"""
solid-name: ForEachMode
solid-category: model
solid-spec: [SPEC-042]
solid-description: Selects individual or batched model presentation without changing per-item workflow execution identity.
"""
class ForEachMode(str, Enum):
    INDIVIDUAL = "individual"
    BATCH = "batch"
