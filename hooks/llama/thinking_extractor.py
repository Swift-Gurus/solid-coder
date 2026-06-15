"""
solid-description: Extracts thinking and content components from LLM response messages.
solid-category: utility
solid-tags: [hook, llm]
"""

import re
from typing import Protocol


class ThinkingExtracting(Protocol):
    def extract(self, message: dict) -> tuple: ...
    def strip(self, content: str) -> tuple: ...


class ThinkingExtractor:
    """Extracts (thinking, content) from LLM response messages."""

    def strip(self, content: str) -> tuple:
        """Split a response that may begin with a <think>…</think> block."""
        if not content:
            return "", content or ""
        match = re.match(r"<think>(.*?)</think>\s*", content, re.DOTALL)
        if match:
            return match.group(1).strip(), content[match.end():].strip()
        return "", content

    def extract(self, message: dict) -> tuple:
        """Extract (thinking, content) preferring reasoning_content over inline think tags."""
        content = message.get("content", "") or ""
        reasoning = message.get("reasoning_content", "") or ""
        if reasoning:
            return reasoning.strip(), content
        return self.strip(content)
