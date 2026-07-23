"""
solid-name: CommandAllowlistValidator
solid-category: service
solid-spec: [SPEC-027]
solid-description: Validates commands against an allowlist.
"""

from __future__ import annotations

from harness.command_allowlist_validating import CommandAllowlistValidating
from harness.models import FlowValidationError


class CommandAllowlistValidator(CommandAllowlistValidating):

    def validate(self, steps: list[dict], allowlist: list[str]) -> None:
        for step in steps:
            if step.get("type") != "script":
                continue
            command = step.get("command") or []
            executable = command[0] if command else None
            if executable not in allowlist:
                raise FlowValidationError(
                    f"Step '{step.get('id')}' command '{executable}' is not on the permitted-executable allowlist"
                )
