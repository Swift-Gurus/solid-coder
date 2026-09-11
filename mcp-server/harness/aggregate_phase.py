"""Defines one aggregate model-execution phase."""

from dataclasses import dataclass, field


"""
solid-name: AggregatePhase
solid-category: model
solid-spec: [SPEC-045]
solid-description: Identifies an ordered set of original model-owned steps compiled within one workflow boundary.
"""
@dataclass(frozen=True)
class AggregatePhase:
    boundary_id: str
    step_ids: list[str] = field(default_factory=list)
