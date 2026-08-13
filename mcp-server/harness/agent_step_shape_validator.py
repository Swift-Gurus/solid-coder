"""Validates the field set of an agent workflow step."""

from __future__ import annotations

from harness.agent_step_field_reading import AgentStepFieldReading
from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.step_field_validating import StepFieldValidating


"""
solid-name: AgentStepShapeValidator
solid-category: service
solid-spec: [SPEC-027]
solid-description: Validates prompt and command fields declared by an agent workflow step.
"""
class AgentStepShapeValidator(StepFieldValidating[AgentStepFieldReading]):
    def __init__(self, error_factory: FlowValidationErrorCreating) -> None:
        self._error_factory = error_factory

    def validate(self, step: AgentStepFieldReading) -> None:
        has_prompt = bool(step.prompt)
        has_prompt_file = bool(step.prompt_file)
        if has_prompt == has_prompt_file:
            raise self._error_factory.create(
                f"Step '{step.id}' must declare exactly one of 'prompt' or 'prompt_file'"
            )
        if step.command:
            raise self._error_factory.create(
                f"Step '{step.id}' is type 'agent' and must not declare 'command'"
            )
