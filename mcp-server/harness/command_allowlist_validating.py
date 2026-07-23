"""
solid-name: CommandAllowlistValidating
solid-category: abstraction
solid-spec: [SPEC-027]
solid-description: Contract for validating items against an allowlist.
"""

from __future__ import annotations

from typing import Protocol

class CommandAllowlistValidating(Protocol):

    def validate(self, steps: list[dict], allowlist: list[str]) -> None: ...
