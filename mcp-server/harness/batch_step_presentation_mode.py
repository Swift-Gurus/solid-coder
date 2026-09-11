"""Defines the supported batch-presentation variants."""

from enum import Enum


"""
solid-name: BatchStepPresentationMode
solid-category: model
solid-spec: [SPEC-042, SPEC-043]
solid-description: Identifies the validation and rendering contract of a model-facing batch presentation.
"""
class BatchStepPresentationMode(str, Enum):
    ORDINARY = "ordinary"
    COMBINED_RULES = "combined_rules"
    AGGREGATE = "aggregate"
