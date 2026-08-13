"""Defines one executable workflow step."""

from __future__ import annotations

from dataclasses import dataclass, field

from harness.output_spec import OutputSpec


"""
solid-name: StepDef
solid-category: model
solid-spec: [SPEC-030, SPEC-027, SPEC-028]
solid-description: Represents a validated workflow step with its execution, dependency, and output contracts.
"""
@dataclass(frozen=True)
class StepDef:
    id: str
    prompt: str
    depends_on: list[str] = field(default_factory=list)
    outputs: list[OutputSpec] = field(default_factory=list)
    for_each: str | None = None
    type: str = "agent"
    mode: str | None = None
    prompt_file: str | None = None
    command: list[str] | str | None = None
    script_file: str | None = None
    executor: str | None = None
    args: list[str] | None = None
    timeout_seconds: int | None = None
    max_attempts: int = 3
