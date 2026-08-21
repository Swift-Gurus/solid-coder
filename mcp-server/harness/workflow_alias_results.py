"""Defines the ordered published results of one include alias."""

from __future__ import annotations

from dataclasses import dataclass, field

from harness.workflow_result_envelope import WorkflowResultEnvelope


"""
solid-name: WorkflowAliasResults
solid-category: model
solid-spec: [SPEC-037]
solid-description: Provides one consistently shaped ordered results collection for an included-workflow alias.
"""
@dataclass(frozen=True)
class WorkflowAliasResults:
    entries: list[WorkflowResultEnvelope] = field(default_factory=list)

    @property
    def results(self) -> "WorkflowAliasResults":
        return self
