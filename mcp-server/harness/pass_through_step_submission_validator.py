"""Accepts workflow step submissions without additional validation."""

from harness.models import FlowDef, StepInstance, ValidationResult
from harness.successful_validation_result_providing import SuccessfulValidationResultProviding


"""
solid-name: PassThroughStepSubmissionValidator
solid-category: service
solid-spec: [SPEC-027, SPEC-035]
solid-description: Accepts workflow step submissions whose outcomes were validated during execution.
"""
class PassThroughStepSubmissionValidator:
    def __init__(
        self,
        success_result_provider: SuccessfulValidationResultProviding,
    ) -> None:
        self._success_result_provider = success_result_provider

    def validate(
        self,
        step_instance: StepInstance,
        outputs: dict,
        flow_def: FlowDef,
    ) -> ValidationResult:
        return self._success_result_provider.provide()
