"""Defines workflow executable allowlist validation."""

from __future__ import annotations

from typing import Protocol

from harness.executable_step_field_reading import ExecutableStepFieldReading


"""
solid-name: CommandAllowlistValidating
solid-category: abstraction
solid-spec: [SPEC-027, SPEC-035]
solid-description: Contract for validating workflow-step executables against an allowlist.
"""
class CommandAllowlistValidating(Protocol):

    def validate(
        self,
        steps: list[ExecutableStepFieldReading],
        allowlist: list[str],
    ) -> None: ...
