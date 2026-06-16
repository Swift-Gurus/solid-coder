"""
solid-description: Contract for constructing output from principles and contextual information.
solid-category: utility
solid-tags: [hook, llm]
"""

from typing import Protocol


class PromptBuilding(Protocol):
    def build(
        self,
        principles: list,
        content: str,
        path: str,
        parent_session_id: str,
        output_dir: str,
    ) -> str: ...
