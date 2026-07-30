"""
solid-name: JsonlinesMessageFormatting
solid-category: abstraction
solid-description: Contract for serializing messages in JSONL format.
"""

from typing import Protocol


class JsonlinesMessageFormatting(Protocol):
    def format(self, msg: dict) -> bytes: ...