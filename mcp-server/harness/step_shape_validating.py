"""
solid-name: StepShapeValidating
solid-category: abstraction
solid-spec: [SPEC-027]
solid-description: Contract for validating steps match their type specifications.
"""

from __future__ import annotations

from typing import Protocol


class StepShapeValidating(Protocol):

    def validate(self, steps: list[dict]) -> None: ...