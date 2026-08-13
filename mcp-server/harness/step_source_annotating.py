"""Defines annotation of expanded steps with their declaring workflow file."""

from typing import Protocol

from harness.sourced_workflow_entry import SourcedWorkflowEntry
from harness.workflow_entry import WorkflowEntry


"""
solid-name: StepSourceAnnotating
solid-category: abstraction
solid-spec: [SPEC-035]
solid-description: Contract for attaching declaring-file provenance to expanded workflow steps.
"""
class StepSourceAnnotating(Protocol):

    def annotate(
        self,
        entries: list[WorkflowEntry],
        source_path: str,
    ) -> list[SourcedWorkflowEntry]:
        ...
