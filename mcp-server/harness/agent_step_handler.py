"""
solid-name: AgentStepHandler
solid-category: service
solid-spec: [SPEC-027]
solid-description: Handles agent-type steps awaiting external input and validates their outputs.
"""

from __future__ import annotations

from harness.models import FlowDef, StepDef, StepInstance, ValidationResult
from harness.step_handling import StepHandling
from harness.step_output_validating import StepOutputValidating
from harness.step_run_outcome import StepRunOutcome


class AgentStepHandler(StepHandling):

    def __init__(self, output_validator: StepOutputValidating) -> None:
        self._output_validator = output_validator

    def run(self, step_instance: StepInstance, step_def: StepDef) -> StepRunOutcome:
        return StepRunOutcome(awaiting_input=True)

    def validate(self, step_instance: StepInstance, outputs: dict, flow_def: FlowDef) -> ValidationResult:
        errors = self._output_validator.validate([step_instance], {step_instance.instance_id: outputs}, flow_def)
        return ValidationResult(ok=not errors, errors=errors)
