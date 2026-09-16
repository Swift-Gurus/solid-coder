"""Defines aggregate assignment fields used by recovery rendering."""

from typing import Protocol

from harness.aggregate_step_rejection_reading import AggregateStepRejectionReading


"""
solid-name: AggregateAssignmentRecoveryReading
solid-category: abstraction
solid-spec: [SPEC-052]
solid-description: Contract for reading an aggregate assignment address and its rejected steps.
"""
class AggregateAssignmentRecoveryReading(Protocol):
    item_label: str
    workflow_alias: str
    rejections: list[AggregateStepRejectionReading]
