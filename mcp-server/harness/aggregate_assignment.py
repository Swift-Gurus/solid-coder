"""Defines one model-visible aggregate workflow assignment."""

from dataclasses import dataclass, field

from harness.aggregate_step_rejection import AggregateStepRejection
from harness.authored_step_reading import AuthoredStepReading


"""
solid-name: AggregateAssignment
solid-category: model
solid-spec: [SPEC-045, SPEC-052]
solid-description: Carries one aggregate item's authored work and correction state.
"""
@dataclass(frozen=True)
class AggregateAssignment:
    item_label: str
    workflow_alias: str
    instance_id: str
    steps: list[AuthoredStepReading] = field(default_factory=list)
    rejections: list[AggregateStepRejection] = field(default_factory=list)
