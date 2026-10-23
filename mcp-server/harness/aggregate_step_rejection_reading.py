"""Defines the rejection fields used by aggregate recovery rendering."""

from typing import Protocol

"""
solid-name: AggregateStepRejectionReading
solid-category: abstraction
solid-spec: [SPEC-052]
solid-description: Contract for representing rejection details during aggregate recovery.
"""


class AggregateStepRejectionReading(Protocol):
    step_id: str
    reason: str
