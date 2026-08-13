"""Defines the fields required to validate a delegate step."""

from __future__ import annotations

from typing import Protocol


"""
solid-name: DelegateStepFieldReading
solid-category: abstraction
solid-spec: [SPEC-027]
solid-description: Contract for reading the fields required to validate a delegate workflow step.
"""
class DelegateStepFieldReading(Protocol):
    id: object | None
    prompt: object | None
    command: object | None
    mode: object | None
