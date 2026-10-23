"""Declares model-facing aggregate-envelope rejection rendering."""

from typing import Protocol

from harness.batch_submission_target import BatchSubmissionTarget

"""
solid-name: AggregateEnvelopeRejectionRendering
solid-category: abstraction
solid-spec: [SPEC-052]
solid-description: Contract for presenting aggregate-submission rejection guidance.
"""


class AggregateEnvelopeRejectionRendering(Protocol):
    def render(
        self,
        reason: str,
        targets: list[BatchSubmissionTarget],
    ) -> str: ...
