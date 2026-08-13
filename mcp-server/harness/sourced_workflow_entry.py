"""Associates a typed workflow entry with its declaring file."""

from dataclasses import dataclass

from harness.workflow_entry import WorkflowEntry


"""
solid-name: SourcedWorkflowEntry
solid-category: model
solid-spec: [SPEC-030, SPEC-035]
solid-description: Carries one parsed workflow entry together with its required declaring-file provenance.
"""
@dataclass(frozen=True)
class SourcedWorkflowEntry:
    entry: WorkflowEntry
    source_file: str
