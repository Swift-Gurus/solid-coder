"""Defines the ordered published results of one include alias."""

from __future__ import annotations

from dataclasses import dataclass, field

from harness.workflow_output_projections import WorkflowOutputProjections
from harness.workflow_result_envelope import WorkflowResultEnvelope

"""
solid-name: WorkflowAliasResults
solid-category: model
solid-spec: [SPEC-037, SPEC-056]
solid-description: Provides ordered child result envelopes and declared output projections for an include alias.
"""


@dataclass(frozen=True)
class WorkflowAliasResults:
    authored_alias: str
    owner_alias: str | None
    runtime_owner_instance_id: str | None
    output_names: list[str] = field(default_factory=list)
    entries: list[WorkflowResultEnvelope] = field(default_factory=list)

    @property
    def results(self) -> WorkflowAliasResults:
        return self

    @property
    def outputs(self) -> WorkflowOutputProjections:
        return WorkflowOutputProjections(
            declared_names=self.output_names,
            entries=[entry.outputs for entry in self.entries],
        )
