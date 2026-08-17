"""Resolves declared child steps into typed runtime identities."""

from harness.included_workflow_step_identity import IncludedWorkflowStepIdentity
from harness.included_workflow_step_identity_resolving import (
    IncludedWorkflowStepIdentityResolving,
)


"""
solid-name: IncludedWorkflowStepIdentityResolver
solid-category: boundary
solid-spec: [SPEC-037]
solid-description: Resolves included workflow child-step declarations into validated local and runtime execution identities.
"""
class IncludedWorkflowStepIdentityResolver(
    IncludedWorkflowStepIdentityResolving,
):
    def resolve(
        self,
        declaration_id: str,
        workflow_alias: str,
        workflow_instance_id: str,
    ) -> IncludedWorkflowStepIdentity:
        qualification = f"{workflow_alias}."
        if not declaration_id.startswith(qualification):
            raise ValueError(
                f"Child step '{declaration_id}' is outside workflow alias "
                f"'{workflow_alias}'"
            )
        local_step_id = declaration_id[len(qualification):]
        if not local_step_id:
            raise ValueError(
                f"Child step '{declaration_id}' has no local identity"
            )
        return IncludedWorkflowStepIdentity(
            declaration_id=declaration_id,
            local_step_id=local_step_id,
            execution_step_id=f"{workflow_instance_id}.{local_step_id}",
        )
