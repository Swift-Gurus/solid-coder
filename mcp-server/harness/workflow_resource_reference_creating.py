"""Defines workflow resource reference creation."""

from typing import Protocol

from harness.workflow_resource_reference import WorkflowResourceReference


"""
solid-name: WorkflowResourceReferenceCreating
solid-category: abstraction
solid-spec: [SPEC-035]
solid-description: Contract for creating a workflow resource reference from its declaration and classified location.
"""
class WorkflowResourceReferenceCreating(Protocol):
    def create(self, declared_value: str) -> WorkflowResourceReference: ...
