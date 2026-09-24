"""Defines one selected source entry for deterministic metric reduction."""

from dataclasses import dataclass

from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: SelectedCollectionMetricEntry
solid-category: model
solid-spec: [SPEC-054]
solid-description: Makes a filtered observation and its source identity available to deterministic metric reducers.
"""
@dataclass(frozen=True)
class SelectedCollectionMetricEntry:
    source_index: int
    value: object
    context: WorkflowRunContext
