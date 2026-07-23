"""
solid-name: StepRunOutcome
solid-category: model
solid-spec: [SPEC-027]
solid-description: Represents the outcome of a step execution.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StepRunOutcome:
    awaiting_input: bool
    outputs: dict | None = None
    rejection_reason: str | None = None