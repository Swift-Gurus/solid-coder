"""
solid-name: CommandAllowlistResolving
solid-category: abstraction
solid-spec: [SPEC-027]
solid-description: Contract for resolving a command allowlist.
"""

from __future__ import annotations

from typing import Protocol


class CommandAllowlistResolving(Protocol):

    def resolve(self) -> list[str]: ...