"""Rejects malformed aggregate envelopes with actionable recovery guidance."""

from harness.aggregate_envelope_rejection_rendering import (
    AggregateEnvelopeRejectionRendering,
)
from harness.aggregate_envelope_submission_rejecting import (
    AggregateEnvelopeSubmissionRejecting,
)
from harness.batch_submission_target import BatchSubmissionTarget
from harness.rejected_step_output_mapping_building import (
    RejectedStepOutputMappingBuilding,
)
from harness.step_output_submission_mapping_result import (
    StepOutputSubmissionMappingResult,
)


"""
solid-name: AggregateEnvelopeSubmissionRejector
solid-category: service
solid-spec: [SPEC-052]
solid-description: Builds rejected aggregate mappings from structural errors and recovery guidance.
"""
class AggregateEnvelopeSubmissionRejector(AggregateEnvelopeSubmissionRejecting):
    def __init__(
        self,
        rejection_renderer: AggregateEnvelopeRejectionRendering,
        rejection_builder: RejectedStepOutputMappingBuilding,
    ) -> None:
        self._rejection_renderer = rejection_renderer
        self._rejection_builder = rejection_builder

    def reject(
        self,
        reason: str,
        targets: list[BatchSubmissionTarget],
    ) -> StepOutputSubmissionMappingResult:
        return self._rejection_builder.build(
            self._rejection_renderer.render(reason, targets)
        )
