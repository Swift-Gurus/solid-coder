"""Defines generation of one metric submission example."""

from typing import Protocol


"""
solid-name: MetricSubmissionExampleBuilding
solid-category: abstraction
solid-description: Contract for producing one LLM-facing metric submission example from its schema declaration.
"""
class MetricSubmissionExampleBuilding(Protocol):
    def build(self, measurement_schema: dict) -> dict: ...
