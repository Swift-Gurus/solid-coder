"""Validates submitted workflow-step outputs."""

from __future__ import annotations

from harness.models import FlowDef, StepInstance
from harness.schema_validator import SchemaValidator
from harness.step_output_validating import StepOutputValidating
from harness.step_output_shape_checking import StepOutputShapeChecking
from harness.step_output_submission_collecting import StepOutputSubmissionCollecting


"""
solid-name: StepOutputValidator
solid-category: service
solid-spec: [SPEC-031, SPEC-039]
solid-description: Coordinates output-container checking, named submission collection, and schema validation.
"""
class StepOutputValidator:

    def __init__(
        self,
        schema_validator: SchemaValidator,
        shape_checker: StepOutputShapeChecking,
        submission_collector: StepOutputSubmissionCollecting,
    ) -> None:
        self._schema_validator = schema_validator
        self._shape_checker = shape_checker
        self._submission_collector = submission_collector

    def validate(
        self,
        ready: list[StepInstance],
        outputs: dict,
        flow_def: FlowDef,
    ) -> list[str]:
        errors = self._shape_checker.errors(ready, outputs)
        submissions = self._submission_collector.collect(
            ready,
            outputs,
            flow_def,
        )
        for submission in submissions:
            result = self._schema_validator.validate(
                submission.specification,
                submission.value,
            )
            if not result.ok:
                identity = (
                    f"{submission.instance_id}."
                    f"{submission.specification.name}"
                )
                errors.extend(
                    f"{identity}: {error}"
                    for error in result.errors
                )
        return errors
