"""Validates workflow process executables against an allowlist."""

from __future__ import annotations

from harness.command_allowlist_validating import CommandAllowlistValidating
from harness.executable_step_field_reading import ExecutableStepFieldReading
from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.step_executable_resolving import StepExecutableResolving


"""
solid-name: CommandAllowlistValidator
solid-category: service
solid-spec: [SPEC-027, SPEC-035]
solid-description: Validates workflow process executables against the permitted-executable allowlist.
"""
class CommandAllowlistValidator(CommandAllowlistValidating):
    def __init__(
        self,
        executable_resolver: StepExecutableResolving,
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._executable_resolver = executable_resolver
        self._error_factory = error_factory

    def validate(
        self,
        steps: list[ExecutableStepFieldReading],
        allowlist: list[str],
    ) -> None:
        for step in steps:
            executable = self._executable_resolver.resolve(step)
            if executable is None:
                continue
            if executable not in allowlist:
                raise self._error_factory.create(
                    f"Step '{step.id}' executable '{executable}' "
                    "is not on the permitted-executable allowlist"
                )
