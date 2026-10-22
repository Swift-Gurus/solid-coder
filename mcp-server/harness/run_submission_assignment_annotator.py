"""Attaches persisted submission addresses to ready workflow instances."""

from dataclasses import replace
from pathlib import Path
from typing import Protocol, TypeVar

from harness.batch_submission_target import BatchSubmissionTarget
from harness.flow_submission_format import FlowSubmissionFormat
from harness.run_metadata_persisting import RunMetadataPersisting
from harness.step_instance import StepInstance
from harness.step_result import StepResult

StepT = TypeVar("StepT", StepInstance, StepResult)


"""
solid-name: RunSubmissionAssignmentAnnotating
solid-category: abstraction
solid-spec: [SPEC-068]
solid-description: Contract for attaching stable run-scoped submission addresses to ready workflow steps.
"""
class RunSubmissionAssignmentAnnotating(Protocol):
    def annotate(self, run_dir: Path, steps: list[StepT]) -> list[StepT]: ...


"""
solid-name: RunSubmissionAssignmentAnnotator
solid-category: service
solid-spec: [SPEC-068]
solid-description: Retains stable short submission addresses across workflow phases, partial retries, and restarts.
"""
class RunSubmissionAssignmentAnnotator(RunSubmissionAssignmentAnnotating):
    def __init__(self, metadata_store: RunMetadataPersisting) -> None:
        self._metadata_store = metadata_store

    def annotate(self, run_dir: Path, steps: list[StepT]) -> list[StepT]:
        metadata = self._metadata_store.read(run_dir)
        if metadata.submission_format is FlowSubmissionFormat.NESTED:
            return steps
        targets = list(metadata.submission_targets)
        annotated: list[StepT] = []
        for step in steps:
            target = next((entry for entry in targets if entry.instance_id == step.instance_id), None)
            if target is None:
                target = BatchSubmissionTarget(
                    label=f"a{len(targets) + 1}",
                    instance_id=step.instance_id,
                    step_id=step.step_id,
                )
                targets.append(target)
            annotated.append(replace(step, submission_id=target.label))
        if targets != metadata.submission_targets:
            self._metadata_store.write(run_dir, replace(metadata, submission_targets=targets))
        return annotated
