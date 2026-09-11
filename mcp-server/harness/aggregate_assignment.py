"""Defines one model-visible aggregate workflow assignment."""

from dataclasses import dataclass, field

from harness.authored_step_coordinate import AuthoredStepCoordinate


"""
solid-name: AggregateAssignment
solid-category: model
solid-spec: [SPEC-045]
solid-description: Associates one opaque item label and workflow alias with ordered authored steps.
"""
@dataclass(frozen=True)
class AggregateAssignment:
    item_label: str
    workflow_alias: str
    instance_id: str
    steps: list[AuthoredStepCoordinate] = field(default_factory=list)
