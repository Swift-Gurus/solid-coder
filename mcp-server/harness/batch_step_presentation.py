"""Defines one model-facing item in a batched workflow step."""

from __future__ import annotations

from dataclasses import dataclass

from harness.aggregate_batch_step_group_identity import (
    AggregateBatchStepGroupIdentity,
)
from harness.batch_step_group_identity import BatchStepGroupIdentity
from harness.batch_step_presentation_mode import BatchStepPresentationMode
from harness.combined_rule_batch_step_group_identity import (
    CombinedRuleBatchStepGroupIdentity,
)

"""
solid-name: BatchStepPresentation
solid-category: model
solid-spec: [SPEC-042]
solid-description: Represents one domain-labelled model-facing batch-step presentation.
"""
@dataclass(frozen=True)
class BatchStepPresentation:
    group: (
        BatchStepGroupIdentity
        | CombinedRuleBatchStepGroupIdentity
        | AggregateBatchStepGroupIdentity
    )
    label: str

    @property
    def mode(self) -> BatchStepPresentationMode:
        return BatchStepPresentationMode.ORDINARY
