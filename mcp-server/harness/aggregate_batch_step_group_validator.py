"""Validates original steps grouped for aggregate presentation."""

from typing import cast

from harness.aggregate_batch_step_presentation import AggregateBatchStepPresentation
from harness.batch_step_group_validating import BatchStepGroupValidating
from harness.flow_validation_error import FlowValidationError
from harness.step_result import StepResult


"""
solid-name: AggregateBatchStepGroupValidator
solid-category: service
solid-spec: [SPEC-045]
solid-description: Enforces unique aggregate item, workflow, and authored-step response addresses.
"""
class AggregateBatchStepGroupValidator(BatchStepGroupValidating):
    def validate(self, steps: list[StepResult]) -> None:
        presentations = [
            cast(AggregateBatchStepPresentation, step.batch)
            for step in steps
        ]
        for index, presentation in enumerate(presentations):
            duplicate = any(
                candidate.label == presentation.label
                and candidate.workflow_alias == presentation.workflow_alias
                and candidate.authored_step.step_id == presentation.authored_step.step_id
                for candidate in presentations[index + 1:]
            )
            if duplicate:
                raise FlowValidationError(
                    "Aggregate item, workflow, and step addresses must be unique"
                )
