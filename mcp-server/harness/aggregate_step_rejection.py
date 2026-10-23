"""Defines one rejected step within an aggregate assignment."""

from dataclasses import dataclass

"""
solid-name: AggregateStepRejection
solid-category: model
solid-spec: [SPEC-052]
solid-description: Represents a rejected aggregate-assignment step and the reason it requires correction.
"""


@dataclass(frozen=True)
class AggregateStepRejection:
    step_id: str
    reason: str
