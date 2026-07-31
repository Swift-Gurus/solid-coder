"""
solid-description: Contract for responding to hook requests through acceptance or rejection.
solid-category: abstraction
"""

from typing import Optional, Protocol


class HookResponding(Protocol):
    def allow(self, additional_context: str = "", updated_input: Optional[dict] = None) -> None: ...
    def block(self, reason: str, additional_context: str = "") -> None: ...
