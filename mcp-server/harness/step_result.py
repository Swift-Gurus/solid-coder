"""
solid-name: StepResult
solid-category: model
solid-spec: [SPEC-013]
solid-description: MCP-facing representation of a step prepared for execution.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StepResult:
    step_id: str
    instance_id: str
    prompt: str
    execution: dict
