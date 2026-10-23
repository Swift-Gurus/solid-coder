"""
solid-description: Parses hook event payloads into structured results.
solid-category: service
solid-tags: [hook]
"""

from collections.abc import Callable


class DefaultHookEventParser:
    """Parses the raw PreToolUse stdin payload via an injected parse function."""

    def __init__(self, parse_fn: Callable) -> None:
        self._parse_fn = parse_fn

    def parse(self, raw: str) -> tuple | None:
        return self._parse_fn(raw)
