"""Defines one child step's local and engine execution identities."""

from dataclasses import dataclass


"""
solid-name: IncludedWorkflowStepIdentity
solid-category: model
solid-spec: [SPEC-037]
solid-description: Associates one child-local step identity with its declaration and opaque engine execution identities.
"""
@dataclass(frozen=True)
class IncludedWorkflowStepIdentity:
    declaration_id: str
    local_step_id: str
    execution_step_id: str
