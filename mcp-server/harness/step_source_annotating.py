"""Defines annotation of expanded steps with their declaring workflow file."""

from typing import Protocol


"""
solid-name: StepSourceAnnotating
solid-category: abstraction
solid-spec: [SPEC-035]
solid-description: Contract for attaching declaring-file provenance to expanded workflow steps.
"""
class StepSourceAnnotating(Protocol):

    def annotate(self, steps: list[dict], source_path: str) -> list[dict]:
        ...
