"""Defines the resolved values published by one workflow instance."""

from __future__ import annotations

from dataclasses import dataclass, field

from harness.resolved_workflow_context_value import ResolvedWorkflowContextValue
from harness.workflow_output_value import WorkflowOutputValue


"""
solid-name: WorkflowOutputValues
solid-category: model
solid-spec: [SPEC-037]
solid-description: Provides typed lookup over the validated outputs published by one workflow instance.
"""
@dataclass(frozen=True)
class WorkflowOutputValues:
    entries: list[WorkflowOutputValue] = field(default_factory=list)

    def find(self, name: str) -> ResolvedWorkflowContextValue[object]:
        for entry in self.entries:
            if entry.name == name:
                return ResolvedWorkflowContextValue(
                    present=True,
                    value=entry.value,
                )
        return ResolvedWorkflowContextValue(present=False)
