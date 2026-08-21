"""Provides typed access to one included workflow instance's step identities."""

from dataclasses import dataclass, field
from typing import Callable

from harness.included_workflow_step_identity import IncludedWorkflowStepIdentity


"""
solid-name: IncludedWorkflowStepIdentities
solid-category: model
solid-spec: [SPEC-037]
solid-description: Finds child workflow step identities by declaration, execution, or local identifiers.
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
        return self._require(
            declaration_id,
            "declaration",
            lambda entry: entry.declaration_id == declaration_id,
        )

    def require_execution(
        self,
        execution_step_id: str,
    ) -> IncludedWorkflowStepIdentity:
        return self._require(
            execution_step_id,
            "execution",
            lambda entry: entry.execution_step_id == execution_step_id,
        )

    def require_local(
        self,
        local_step_id: str,
    ) -> IncludedWorkflowStepIdentity:
        return self._require(
            local_step_id,
            "local",
            lambda entry: entry.local_step_id == local_step_id,
        )

    def _require(
        self,
        identity: str,
        kind: str,
        matches: Callable[[IncludedWorkflowStepIdentity], bool],
    ) -> IncludedWorkflowStepIdentity:
        for entry in self.entries:
            if matches(entry):
                return entry
        raise ValueError(
            f"Included workflow {kind} identity not found: '{identity}'"
        )
