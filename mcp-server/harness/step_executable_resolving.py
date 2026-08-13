"""Defines executable resolution from workflow step declarations."""

from __future__ import annotations

from typing import Protocol

from harness.executable_step_field_reading import ExecutableStepFieldReading


"""
solid-name: StepExecutableResolving
solid-category: abstraction
solid-spec: [SPEC-035]
solid-description: Contract for resolving the permitted executable declared by a workflow process step.
"""
class StepExecutableResolving(Protocol):
    def resolve(self, step: ExecutableStepFieldReading) -> str | None: ...
