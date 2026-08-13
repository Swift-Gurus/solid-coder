"""Defines collection of declaring-file provenance from workflow steps."""

from typing import Protocol


"""
solid-name: StepSourceCollecting
solid-category: abstraction
solid-spec: [SPEC-035]
solid-description: Contract for collecting unique declaring-file sources from resolved workflow steps.
"""
class StepSourceCollecting(Protocol):
    def collect(self, steps: list[dict], existing_sources: list[str]) -> list[str]: ...
