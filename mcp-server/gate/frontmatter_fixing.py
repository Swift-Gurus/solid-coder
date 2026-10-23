"""
solid-description: Contract for fixing frontmatter in written content.
solid-category: abstraction
solid-tags: [hook]
"""

from typing import Protocol


class FrontmatterFixing(Protocol):
    def fix(self, content: str, session_id: str, path: str) -> str | None: ...
