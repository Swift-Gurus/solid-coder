"""Renders actionable recovery for malformed aggregate envelopes."""

from harness.aggregate_envelope_rejection_rendering import (
    AggregateEnvelopeRejectionRendering,
)
from harness.batch_submission_target import BatchSubmissionTarget


"""
solid-name: AggregateEnvelopeRejectionRenderer
solid-category: service
solid-spec: [SPEC-052]
solid-description: Explains full resubmission after structural aggregate rejection.
"""
class AggregateEnvelopeRejectionRenderer(AggregateEnvelopeRejectionRendering):
    def render(
        self,
        reason: str,
        targets: list[BatchSubmissionTarget],
    ) -> str:
        addresses = "\n".join(
            f"- {target.label} / {target.workflow_alias} / {target.step_id}"
            for target in targets
        )
        return (
            f"{reason}\n"
            "No assignments from this call were saved. Resubmit the complete "
            "aggregate JSON, not a partial correction. Use the exact schema from "
            "the preceding flow_start or flow_next response. The top-level keys "
            "must be item labels; do not wrap the object in a step ID or workflow "
            "alias.\n"
            f"Allowed item / workflow / step addresses:\n{addresses}"
        )
