"""Defines one durable skipped workflow-step decision."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from harness.condition_declaration import ConditionDeclaration


"""
solid-name: StepSkip
solid-category: model
solid-spec: [SPEC-037]
solid-description: Captures a durable workflow-step skip decision, including its identity, context, and governing condition.
"""
@dataclass(frozen=True)
class StepSkip:
    step_id: str
    instance_id: str
    condition: ConditionDeclaration
    item: Any = None
    iteration_index: int | None = None
