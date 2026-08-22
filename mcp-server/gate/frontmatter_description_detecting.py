"""Defines prospective frontmatter-description detection."""

from typing import Protocol


"""
solid-name: FrontmatterDescriptionDetecting
solid-category: abstraction
solid-description: Contract for detecting authored frontmatter descriptions in prospective source content.
solid-tags: [hook]
"""
class FrontmatterDescriptionDetecting(Protocol):
    def detects(self, content: str) -> bool: ...
