"""Defines the fields required to validate a script step."""

from __future__ import annotations

from typing import Protocol


"""
solid-name: ScriptStepFieldReading
solid-category: abstraction
solid-spec: [SPEC-027, SPEC-035]
solid-description: Contract for reading the fields required to validate a script workflow step.
"""
class ScriptStepFieldReading(Protocol):
    id: object | None
    prompt: object | None
    prompt_file: object | None
    command: object | None
    script_file: object | None
    executor: object | None
    args: object | None
