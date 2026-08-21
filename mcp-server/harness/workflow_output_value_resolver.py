"""Resolves and validates one published workflow-output value."""

from __future__ import annotations

from harness.included_workflow_instance import IncludedWorkflowInstance
from harness.interpolation_error import InterpolationError
from harness.schema_validator import SchemaValidator
from harness.workflow_output_declaration import WorkflowOutputDeclaration
from harness.workflow_output_value import WorkflowOutputValue
from harness.workflow_output_value_resolving import WorkflowOutputValueResolving
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: WorkflowOutputValueResolver
solid-category: service
solid-spec: [SPEC-037]
solid-description: Resolves and validates one declared output from a completed workflow instance.
"""
class WorkflowOutputValueResolver(WorkflowOutputValueResolving):

    def __init__(self, schema_validator: SchemaValidator) -> None:
        self._schema_validator = schema_validator

    def resolve(
        self,
        instance: IncludedWorkflowInstance,
        output: WorkflowOutputDeclaration,
        context: WorkflowRunContext,
    ) -> WorkflowOutputValue:
        identity = instance.steps.require_local(output.reference.step_id)
        completed = context.completed_steps.find(identity.execution_step_id)
        skipped = context.skipped_steps.find(identity.execution_step_id)
        if completed.present and completed.value is not None:
            if not completed.value.contains(output.reference.output_name):
                raise InterpolationError(
                    f"Workflow instance '{instance.instance_id}' output "
                    f"'{output.specification.name}' references a missing value"
                )
            value = completed.value.get(output.reference.output_name)
        elif (
            skipped.present
            and skipped.value is not None
            and skipped.value.iteration_index is not None
        ):
            value = []
        else:
            raise InterpolationError(
                f"Workflow instance '{instance.instance_id}' did not complete "
                f"output step '{output.reference.step_id}'"
            )
        validation = self._schema_validator.validate(
            output.specification,
            value,
        )
        if not validation.ok:
            raise InterpolationError(
                f"Workflow instance '{instance.instance_id}' output "
                f"'{output.specification.name}' is invalid: "
                + "; ".join(validation.errors)
            )
        return WorkflowOutputValue(
            name=output.specification.name,
            value=value,
        )
