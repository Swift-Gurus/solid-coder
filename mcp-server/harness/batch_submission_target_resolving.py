"""Declares exact batch-submission target resolution."""

from __future__ import annotations

from typing import Protocol

from harness.batch_submission_target import BatchSubmissionTarget


"""
solid-name: BatchSubmissionTargetResolving
solid-category: abstraction
solid-spec: [SPEC-045]
solid-description: Contract for resolving a model-visible batch address to an original workflow-step instance.
"""
class BatchSubmissionTargetResolving(Protocol):
    def resolve(
        self,
        targets: list[BatchSubmissionTarget],
        label: str,
        workflow_alias: str,
        step_id: str,
    ) -> BatchSubmissionTarget | None: ...
