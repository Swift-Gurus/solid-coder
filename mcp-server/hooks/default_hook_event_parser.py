"""
solid-description: Parses hook event payloads into structured results.
solid-category: service
solid-tags: [hook]
"""

from typing import Callable, Optional


class DefaultHookEventParser:
    """Parses the raw PreToolUse stdin payload via an injected parse function."""

    def __init__(self, parse_fn: Callable) -> None:
        self._parse_fn = parse_fn

    def parse(self, raw: str) -> Optional[tuple]:
        return self._parse_fn(raw)