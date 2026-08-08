"""Defines incomplete unit coverage for a findings batch."""

from dataclasses import dataclass


"""
solid-name: BatchCoverageFailure
solid-category: model
solid-description: Identifies principles that omitted required source units from a batch review submission.
"""
@dataclass(frozen=True)
class BatchCoverageFailure:
    principle_labels: tuple[str, ...]
    expected_units: tuple[str, ...]
