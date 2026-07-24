"""
solid-name: StepFieldValidating
solid-category: abstraction
solid-spec: [SPEC-027]
solid-description: Contract for validating a step's field set.
"""

from __future__ import annotations

from typing import Protocol


class StepFieldValidating(Protocol):

    def validate(self, step: dict) -> None: ...
