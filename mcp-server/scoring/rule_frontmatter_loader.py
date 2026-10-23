"""Loads raw frontmatter from a principle rule source."""

from collections.abc import Callable
from pathlib import Path

from utils.prompt_builder import TextFileReading

from scoring.rule_frontmatter_loading import RuleFrontmatterLoading

"""
solid-name: RuleFrontmatterLoader
solid-category: boundary-adapter
solid-description: Reads a principle rule source and extracts its raw frontmatter text.
"""


class RuleFrontmatterLoader(RuleFrontmatterLoading):
    def __init__(
        self,
        reader: TextFileReading,
        extractor: Callable[[str], str | None],
    ) -> None:
        self._reader = reader
        self._extractor = extractor

    def load(self, rule_path: Path) -> str | None:
        content = self._reader.read(rule_path)
        return None if content is None else self._extractor(content)
