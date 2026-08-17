"""Provides typed access to one included workflow instance's step identities."""

from dataclasses import dataclass, field

from harness.included_workflow_step_identity import IncludedWorkflowStepIdentity


"""
solid-name: IncludedWorkflowStepIdentities
solid-category: model
solid-spec: [SPEC-037]
solid-description: Stores child step identities and resolves declaration identities without exposing their execution encoding.
"""
@dataclass(frozen=True)
class IncludedWorkflowStepIdentities:
    entries: list[IncludedWorkflowStepIdentity] = field(default_factory=list)

    def contains_declaration(self, declaration_id: str) -> bool:
        return any(
            entry.declaration_id == declaration_id
            for entry in self.entries
        )

    def require_declaration(
        self,
        declaration_id: str,
    ) -> IncludedWorkflowStepIdentity:
        for entry in self.entries:
            if entry.declaration_id == declaration_id:
                return entry
        raise ValueError(
            f"Included workflow step identity not found: '{declaration_id}'"
        )

    def require_execution(
        self,
        execution_step_id: str,
    ) -> IncludedWorkflowStepIdentity:
        for entry in self.entries:
            if entry.execution_step_id == execution_step_id:
                return entry
        raise ValueError(
            f"Included workflow execution identity not found: '{execution_step_id}'"
        )
