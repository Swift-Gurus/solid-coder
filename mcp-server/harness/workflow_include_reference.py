"""Defines a stable workflow-ID include reference."""

from dataclasses import dataclass


"""
solid-name: WorkflowIncludeReference
solid-category: model
solid-spec: [SPEC-035]
solid-description: Identifies a workflow included through its globally unique catalog ID.
"""
@dataclass(frozen=True)
class WorkflowIncludeReference:
    workflow: str
