"""Defines the source association for one included workflow instance."""

from dataclasses import dataclass


"""
solid-name: IncludedWorkflowInstance
solid-category: model
solid-spec: [SPEC-037]
solid-description: Identifies one materialized included workflow and associates it with its source position and value.
"""
@dataclass(frozen=True)
class IncludedWorkflowInstance:
    alias: str
    instance_id: str
    source_index: int
    source_item: object
