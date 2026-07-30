"""
solid-name: TerminalMessageResolving
solid-category: abstraction
solid-spec: [SPEC-013]
solid-description: Contract for determining the message to display when a flow reaches a terminal state, or None if it hasn't.
"""

from __future__ import annotations

from typing import Protocol


class TerminalMessageResolving(Protocol):
    def resolve(self, error: str | None, status: str | None) -> str | None: ...