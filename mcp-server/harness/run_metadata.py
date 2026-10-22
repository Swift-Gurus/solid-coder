"""
solid-name: RunMetadata
solid-category: model
solid-spec: [SPEC-031]
solid-description: Represents metadata for a run execution.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from harness.batch_submission_target import BatchSubmissionTarget
from harness.flow_submission_format import FlowSubmissionFormat


@dataclass(frozen=True)
class RunMetadata:
    params: dict
    submission_format: FlowSubmissionFormat = FlowSubmissionFormat.NESTED
    submission_targets: list[BatchSubmissionTarget] = field(default_factory=list)
