"""Defines the fields required to validate an inline-command step."""

from __future__ import annotations

from typing import Protocol


"""
solid-name: CommandStepFieldReading
solid-category: abstraction
solid-spec: [SPEC-035]
solid-description: Contract for reading the fields required to validate an inline-command workflow step.
"""
class CommandStepFieldReading(Protocol):
    id: object | None
    prompt: object | None
    prompt_file: object | None
    command: object | None
    script_file: object | None
    executor: object | None
    args: object | None
