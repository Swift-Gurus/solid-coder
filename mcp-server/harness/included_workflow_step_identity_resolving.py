"""Defines construction of typed child workflow step identities."""

from typing import Protocol

from harness.included_workflow_step_identity import IncludedWorkflowStepIdentity


"""
solid-name: IncludedWorkflowStepIdentityResolving
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for resolving one declared child step into local and opaque execution identities.
"""
class IncludedWorkflowStepIdentityResolving(Protocol):
    def resolve(
        self,
        declaration_id: str,
        workflow_alias: str,
        workflow_instance_id: str,
    ) -> IncludedWorkflowStepIdentity: ...
