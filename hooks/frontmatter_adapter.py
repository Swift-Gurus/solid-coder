"""
solid-description: Boundary adapter wrapping validate_swift_frontmatter.fix to the FrontmatterFixing protocol.
solid-category: service
solid-tags: [hook]
"""

from typing import Callable, Optional


class FrontmatterAdapter:
    """Boundary adapter: wraps the frontmatter module-level function for protocol-typed injection."""

    def __init__(self, fix_fn: Callable) -> None:
        self._fix = fix_fn

    def fix(self, content: str, session_id: str, path: str) -> Optional[str]:
        return self._fix(content, parent_session_id=session_id)
