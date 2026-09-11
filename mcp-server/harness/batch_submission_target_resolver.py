"""Resolves an exact batch address to its original instance."""

from __future__ import annotations

from harness.batch_submission_target import BatchSubmissionTarget
from harness.batch_submission_target_resolving import BatchSubmissionTargetResolving


"""
solid-name: BatchSubmissionTargetResolver
solid-category: service
solid-spec: [SPEC-045]
solid-description: Resolves item, workflow, and step addresses against known batch submission targets.
"""
class BatchSubmissionTargetResolver(BatchSubmissionTargetResolving):
    def resolve(
        self,
        targets: list[BatchSubmissionTarget],
        label: str,
        workflow_alias: str,
        step_id: str,
    ) -> BatchSubmissionTarget | None:
        return next(
            (
                target
                for target in targets
                if target.label == label
                and target.workflow_alias == workflow_alias
                and target.step_id == step_id
            ),
            None,
        )
