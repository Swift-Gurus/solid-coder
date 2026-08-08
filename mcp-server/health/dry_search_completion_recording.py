"""Defines recording of successful health-check DRY searches."""

from typing import Protocol


"""
solid-name: DrySearchCompletionRecording
solid-category: abstraction
solid-description: Contract for recording successful DRY search completion for one health-check output directory.
"""
class DrySearchCompletionRecording(Protocol):
    def record(self, output_dir: str) -> None: ...
