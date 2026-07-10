"""
solid-description: Contract for sending Claude PreToolUse hook protocol responses.
solid-category: abstraction
"""

from typing import Protocol


class HookResponding(Protocol):
    def allow(self) -> None: ...
    def block(self, reason: str, additional_context: str = "") -> None: ...
    def allow_with_update(self, updated_input: dict) -> None: ...
