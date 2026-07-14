"""
solid-description: Contract for determining whether content should be processed for frontmatter correction.
solid-category: abstraction
solid-tags: [hook]
"""

from typing import Optional, Protocol


class FileTypePolicy(Protocol):
    """Decides whether a tool call's content is in scope for frontmatter correction."""

    def content_for(self, tool_name: str, tool_input: dict) -> Optional[str]: ...

    def should_process(self, file_path: str, content: str) -> bool: ...
