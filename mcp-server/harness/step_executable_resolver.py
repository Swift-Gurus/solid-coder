"""Resolves permitted executables from workflow process steps."""

from __future__ import annotations

from typing import cast

from harness.executable_step_field_reading import ExecutableStepFieldReading


"""
solid-name: StepExecutableResolver
solid-category: service
solid-spec: [SPEC-027, SPEC-035]
solid-description: Resolves the executable selected by a workflow process step declaration.
"""
class StepExecutableResolver:
    _DEFAULT_EXECUTOR = "bash"

    def resolve(self, step: ExecutableStepFieldReading) -> str | None:
        if step.type == "command" or step.script_file is not None:
            return cast(str, step.executor or self._DEFAULT_EXECUTOR)
        if step.type == "script":
            command = cast(list[str], step.command or [])
            return command[0] if command else None
        return None
