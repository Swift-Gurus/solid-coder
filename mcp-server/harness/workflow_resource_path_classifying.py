"""Defines workflow resource path classification."""

from typing import Protocol

from harness.workflow_resource_path_classification import WorkflowResourcePathClassification


"""
solid-name: WorkflowResourcePathClassifying
solid-category: abstraction
solid-spec: [SPEC-035]
solid-description: Contract for identifying the resolution anchor and path carried by a workflow resource declaration.
"""
class WorkflowResourcePathClassifying(Protocol):
    def classify(self, declared_value: str) -> WorkflowResourcePathClassification: ...
