"""Defines one original step participating in aggregate presentation."""

from dataclasses import dataclass

from harness.authored_step_coordinate import AuthoredStepCoordinate
from harness.batch_step_presentation import BatchStepPresentation
from harness.batch_step_presentation_mode import BatchStepPresentationMode


"""
solid-name: AggregateBatchStepPresentation
solid-category: model
solid-spec: [SPEC-045]
solid-description: Associates an original ready step with its aggregate item, workflow, and authored-step identities.
"""
@dataclass(frozen=True)
class AggregateBatchStepPresentation(BatchStepPresentation):
    workflow_alias: str
    authored_step: AuthoredStepCoordinate

    @property
    def mode(self) -> BatchStepPresentationMode:
        return BatchStepPresentationMode.AGGREGATE
