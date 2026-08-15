"""Defines model-facing status for one skipped workflow-step instance."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


"""
solid-name: StepSkipStatus
solid-category: model
solid-spec: [SPEC-037]
solid-description: Captures the identity, context, and condition summary of a skipped step instance.
"""
@dataclass(frozen=True)
class StepSkipStatus:
    step_id: str
    instance_id: str
    condition: dict[str, object]
    item: Any = None
    iteration_index: int | None = None
