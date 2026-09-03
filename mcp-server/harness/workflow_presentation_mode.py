"""Defines model-facing presentation modes for workflow groups."""

from enum import Enum


"""
solid-name: WorkflowPresentationMode
solid-category: model
solid-spec: [SPEC-043]
solid-description: Selects whether a workflow group presents each child independently or combines compatible child rules in one model turn.
"""
class WorkflowPresentationMode(str, Enum):
    INDIVIDUAL = "individual"
    COMBINED = "combined"
