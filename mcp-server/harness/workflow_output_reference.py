"""Defines a typed reference to projected included-workflow outputs."""

from dataclasses import dataclass


"""
solid-name: WorkflowOutputReference
solid-category: model
solid-spec: [SPEC-056]
solid-description: Identifies one declared output projected across an included workflow alias.
"""
@dataclass(frozen=True)
class WorkflowOutputReference:
    workflow_alias: str
    output_name: str
