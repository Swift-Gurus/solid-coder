"""Coordinates resolution of published workflow-output values."""

from __future__ import annotations

from harness.included_workflow_instance import IncludedWorkflowInstance
from harness.workflow_output_declaration import WorkflowOutputDeclaration
from harness.workflow_output_value_resolving import WorkflowOutputValueResolving
from harness.workflow_output_values import WorkflowOutputValues
from harness.workflow_output_values_resolving import WorkflowOutputValuesResolving
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: WorkflowOutputValuesResolver
solid-category: service
solid-spec: [SPEC-037]
solid-description: Coordinates resolution of the declared outputs published by one workflow instance.
"""
class WorkflowOutputValuesResolver(WorkflowOutputValuesResolving):

    def __init__(self, value_resolver: WorkflowOutputValueResolving) -> None:
        self._value_resolver = value_resolver

    def resolve(
        self,
        instance: IncludedWorkflowInstance,
        outputs: list[WorkflowOutputDeclaration],
        context: WorkflowRunContext,
    ) -> WorkflowOutputValues:
        return WorkflowOutputValues(entries=[
            self._value_resolver.resolve(instance, output, context)
            for output in outputs
        ])
