"""Assembles workflow-results context construction."""

from __future__ import annotations

from harness.included_workflow_instances_resolver import (
    IncludedWorkflowInstancesResolver,
)
from harness.schema_validator import SchemaValidator
from harness.step_terminal_state_resolver import StepTerminalStateResolver
from harness.workflow_output_value_resolver import WorkflowOutputValueResolver
from harness.workflow_output_values_resolver import WorkflowOutputValuesResolver
from harness.workflow_publication_state_resolver import (
    WorkflowPublicationStateResolver,
)
from harness.workflow_result_envelope_builder import WorkflowResultEnvelopeBuilder
from harness.workflow_results_context_builder import WorkflowResultsContextBuilder


"""
solid-name: WorkflowResultsContextBuilderFactory
solid-category: factory
solid-spec: [SPEC-037]
solid-description: Assembles workflow-results context construction with terminal-state and output-validation collaborators.
"""
class WorkflowResultsContextBuilderFactory:
    def make(
        self,
        schema_validator: SchemaValidator,
    ) -> WorkflowResultsContextBuilder:
        return WorkflowResultsContextBuilder(
            instances_resolver=IncludedWorkflowInstancesResolver(),
            envelope_builder=WorkflowResultEnvelopeBuilder(
                publication_state_resolver=WorkflowPublicationStateResolver(
                    terminal_state_resolver=StepTerminalStateResolver(),
                ),
                output_values_resolver=WorkflowOutputValuesResolver(
                    value_resolver=WorkflowOutputValueResolver(
                        schema_validator=schema_validator,
                    ),
                ),
            ),
        )
