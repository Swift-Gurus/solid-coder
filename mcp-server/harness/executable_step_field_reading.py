"""Defines fields required to resolve a workflow-step executable."""

from __future__ import annotations

from typing import Protocol


"""
solid-name: ExecutableStepFieldReading
solid-category: abstraction
solid-spec: [SPEC-027, SPEC-035]
solid-description: Contract for reading workflow-step type and executable-selection fields.
"""
class ExecutableStepFieldReading(Protocol):
    id: object | None
    type: object
    command: object | None
    script_file: object | None
    executor: object | None
