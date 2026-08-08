"""
solid-name: StepFormatting
solid-category: abstraction
solid-spec: [SPEC-031]
solid-description: Contract for converting step execution information into formatted text output.
"""

from __future__ import annotations

from typing import Protocol


class StepFormatting(Protocol):
    def format(self, instance_id: str, body: str, rejection_reason: str | None) -> str: ...
