"""Defines the fields required to validate an agent step."""

from __future__ import annotations

from typing import Protocol


"""
solid-name: AgentStepFieldReading
solid-category: abstraction
solid-spec: [SPEC-027]
solid-description: Contract for reading the fields required to validate an agent workflow step.
"""
class AgentStepFieldReading(Protocol):
    id: object | None
    prompt: object | None
    prompt_file: object | None
    command: object | None
