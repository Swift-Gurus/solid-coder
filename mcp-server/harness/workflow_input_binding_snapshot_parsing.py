"""Defines restoration of one workflow input binding."""

from typing import Protocol

from harness.workflow_input_binding import WorkflowInputBinding


"""
solid-name: WorkflowInputBindingSnapshotParsing
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for restoring one child input binding from a workflow snapshot.
"""
class WorkflowInputBindingSnapshotParsing(Protocol):
    def parse(self, raw: object, alias: str) -> WorkflowInputBinding: ...
