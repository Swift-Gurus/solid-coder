"""Defines loading of raw frontmatter from a principle rule source."""

from pathlib import Path
from typing import Protocol

"""
solid-name: RuleFrontmatterLoading
solid-category: abstraction
solid-description: Contract for loading raw frontmatter text from a principle rule source.
"""


class RuleFrontmatterLoading(Protocol):
    def load(self, rule_path: Path) -> str | None: ...
