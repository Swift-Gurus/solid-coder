"""
solid-description: Contract for parsing hook event information.
solid-category: abstraction
solid-tags: [hook]
"""

from typing import Protocol


class HookEventParsing(Protocol):
    """Parses the raw PreToolUse stdin payload into (tool_name, tool_input, file_path, session_id, cwd)."""

    def parse(self, raw: str) -> tuple | None: ...
