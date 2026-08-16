"""Provides typed lookup over named workflow-context values."""

from dataclasses import dataclass, field
from typing import Generic, TypeVar

from harness.resolved_workflow_context_value import ResolvedWorkflowContextValue
from harness.workflow_context_value import WorkflowContextValue


Value = TypeVar("Value")


"""
solid-name: WorkflowContextValues
solid-category: model
solid-spec: [SPEC-030, SPEC-037]
solid-description: Resolves typed named values from one workflow runtime context collection.
"""
@dataclass(frozen=True)
class WorkflowContextValues(Generic[Value]):
    entries: list[WorkflowContextValue[Value]] = field(default_factory=list)

    def find(self, name: str) -> ResolvedWorkflowContextValue[Value]:
        for entry in self.entries:
            if entry.name == name:
                return ResolvedWorkflowContextValue(
                    present=True,
                    value=entry.value,
                )
        return ResolvedWorkflowContextValue(present=False)
