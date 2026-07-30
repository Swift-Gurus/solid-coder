"""
solid-name: TerminalMessageResolver
solid-category: service
solid-spec: [SPEC-013]
solid-description: Resolves the terminal message to display when a flow completes.
"""

from __future__ import annotations

from harness.terminal_message_resolving import TerminalMessageResolving

_TERMINAL_MESSAGES = {
    "done": "Flow complete.",
}


class TerminalMessageResolver(TerminalMessageResolving):

    def resolve(self, error: str | None, status: str | None) -> str | None:
        if error:
            return error
        return _TERMINAL_MESSAGES.get(status)
