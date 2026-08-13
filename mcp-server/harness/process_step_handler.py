"""Coordinates process-backed workflow step handling."""

from harness.models import FlowDef, StepDef, StepInstance, ValidationResult
from harness.step_handling import StepHandling
from harness.step_running import StepRunning
from harness.step_run_outcome import StepRunOutcome
from harness.step_submission_validating import StepSubmissionValidating


"""
solid-name: ProcessStepHandler
solid-category: service
solid-spec: [SPEC-027, SPEC-035]
solid-description: Coordinates execution and submission validation for process-backed workflow steps.
"""
class ProcessStepHandler(StepHandling):
    def __init__(
        self,
        executor: StepRunning,
        submission_validator: StepSubmissionValidating,
    ) -> None:
        self._executor = executor
        self._submission_validator = submission_validator

    def run(self, step_instance: StepInstance, step_def: StepDef) -> StepRunOutcome:
        return self._executor.run(step_instance, step_def)

    def validate(
        self,
        step_instance: StepInstance,
        outputs: dict,
        flow_def: FlowDef,
    ) -> ValidationResult:
        return self._submission_validator.validate(step_instance, outputs, flow_def)
