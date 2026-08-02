"""
solid-name: PreReadEventReader
solid-category: service
solid-description: Reads a preloaded event.
solid-tags: [hook]
"""

from __future__ import annotations


class PreReadEventReader:

    def __init__(self, event: dict) -> None:
        self._event = event

    def read(self) -> dict:
        return self._event
