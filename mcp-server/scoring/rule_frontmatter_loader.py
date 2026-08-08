"""Loads raw frontmatter from a principle rule source."""

from pathlib import Path
from typing import Callable, Optional

from scoring.rule_frontmatter_loading import RuleFrontmatterLoading
from utils.prompt_builder import TextFileReading


"""
solid-name: RuleFrontmatterLoader
solid-category: boundary-adapter
solid-description: Reads a principle rule source and extracts its raw frontmatter text.
"""
class RuleFrontmatterLoader(RuleFrontmatterLoading):
    def __init__(
        self,
        reader: TextFileReading,
        extractor: Callable[[str], Optional[str]],
    ) -> None:
        self._reader = reader
        self._extractor = extractor

    def load(self, rule_path: Path) -> Optional[str]:
        content = self._reader.read(rule_path)
        return None if content is None else self._extractor(content)
