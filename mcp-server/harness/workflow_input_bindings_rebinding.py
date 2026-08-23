"""Defines immutable workflow-input binding substitution."""

from typing import Protocol

from harness.workflow_input_binding import WorkflowInputBinding


"""
solid-name: WorkflowInputBindingsRebinding
solid-category: abstraction
solid-spec: [SPEC-037, SPEC-039]
solid-description: Contract for replacing one workflow input expression from another authored binding.
"""
class WorkflowInputBindingsRebinding(Protocol):
    def rebind(
        self,
        bindings: list[WorkflowInputBinding],
    ) -> list[WorkflowInputBinding]: ...
