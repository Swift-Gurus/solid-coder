"""Maps flat records to the existing canonical output boundary."""

from harness.flow_validation_error import FlowValidationError
from harness.step_instance import StepInstance
from harness.step_output_submission_mapping import StepOutputSubmissionMapping
from harness.step_output_submission_mapping_result import (
    StepOutputSubmissionMappingResult,
)
from harness.structured_model_decoding import StructuredModelDecoding
from harness.submissions.flat_submission_envelope import FlatSubmissionEnvelope

"""
solid-name: FlatStepOutputSubmissionMapper
solid-category: boundary-adapter
solid-spec: [SPEC-068]
solid-description: Validates flat assignment addresses before translating opaque named outputs into existing step-instance submissions.
"""


class FlatStepOutputSubmissionMapper(StepOutputSubmissionMapping):
    def __init__(
        self, decoder: StructuredModelDecoding[FlatSubmissionEnvelope]
    ) -> None:
        self._decoder = decoder

    def map(
        self, ready: list[StepInstance], outputs: dict
    ) -> StepOutputSubmissionMappingResult:
        if not outputs:
            return StepOutputSubmissionMappingResult(outputs={})
        try:
            envelope = self._decoder.decode(outputs, "flat submissions envelope")
        except FlowValidationError as error:
            return StepOutputSubmissionMappingResult(
                outputs={},
                error=(
                    f"{error}\nNothing was accepted. Resubmit outputs as "
                    '{"submissions": [{"id": "<current ID>", "result": {"<named output>": "<value>"}}]}. '
                    "Each result must contain that assignment's complete named outputs."
                ),
            )
        selected = ready[0] if ready else None
        eligible = [
            step
            for step in ready
            if step is selected
            or (
                selected is not None
                and selected.batch is not None
                and step.batch is not None
                and step.batch.group == selected.batch.group
            )
        ]
        submitted_ids = [record.id for record in envelope.submissions]
        if len(set(submitted_ids)) != len(submitted_ids):
            return StepOutputSubmissionMappingResult(
                outputs={},
                error="Duplicate submission ID. Nothing was accepted; resend each pending ID at most once with its complete result.",
            )
        eligible_ids = [step.submission_id for step in eligible]
        unknown = [
            identity for identity in submitted_ids if identity not in eligible_ids
        ]
        if unknown:
            return StepOutputSubmissionMappingResult(
                outputs={},
                error=f"Unknown, stale, or unpresented submission IDs: {unknown}. Nothing was accepted. Use only current IDs: {eligible_ids}.",
            )
        return StepOutputSubmissionMappingResult(
            outputs={
                step.instance_id: record.result
                for record in envelope.submissions
                for step in eligible
                if step.submission_id == record.id
            }
        )
