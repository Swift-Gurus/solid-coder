"""Defines one ready execution of a workflow step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


"""
solid-name: StepInstance
solid-category: model
solid-spec: [SPEC-030]
solid-description: Represents a ready step execution with its instance identity, item binding, and rendered prompt.
"""
@dataclass(frozen=True)
class StepInstance:
    step_id: str
    instance_id: str
    item: Any
    prompt: str
