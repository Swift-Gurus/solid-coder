"""Defines one rejected step within an aggregate assignment."""

from dataclasses import dataclass


"""
solid-name: AggregateStepRejection
solid-category: model
solid-spec: [SPEC-052]
solid-description: Carries an aggregate step identifier and its correction reason.
"""
@dataclass(frozen=True)
class AggregateStepRejection:
    step_id: str
    reason: str
