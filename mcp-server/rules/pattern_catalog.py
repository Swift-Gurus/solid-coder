#!/usr/bin/env python3
"""
solid-description: Builds a formatted catalog of design patterns organized by category.
solid-category: utility
solid-tags: [utility, service]
"""

from pathlib import Path
from typing import Optional, Protocol


class FrontmatterParsing(Protocol):
    def parse(self, path: str) -> dict: ...


class PatternCatalogBuilder:
    """Renders a compact catalog of all design patterns in a directory.

    Instantiate with the patterns root directory. Pass a frontmatter_parser
    for testing; omit (or pass None) to use the default spec.parse_frontmatter.
    """

    def __init__(self, patterns_root: Path, frontmatter_parser: Optional[FrontmatterParsing] = None) -> None:
        self._patterns_root = patterns_root
        if frontmatter_parser is None:
            from spec import parse_frontmatter
            self._fm_parser: FrontmatterParsing = parse_frontmatter
        else:
            self._fm_parser = frontmatter_parser

    def build(self) -> str:
        """Render a compact catalog of all design patterns.

        Returns:
            Catalog string with one entry per pattern. Empty string if no patterns found.
        """
        if not self._patterns_root.is_dir():
            return ""

        by_category: dict[str, list[tuple[str, str, str]]] = {}
        for path in sorted(self._patterns_root.glob("*/*.md")):
            try:
                fm = self._fm_parser.parse(str(path))
            except Exception:
                continue
            name = fm.get("displayName") or fm.get("name") or path.stem
            desc = (fm.get("description") or "").strip()
            category = fm.get("category") or path.parent.name
            by_category.setdefault(category, []).append((name, desc, str(path)))

        if not by_category:
            return ""

        lines: list[str] = [
            "# Design Patterns Index",
            "",
            "Consult this catalog when you need to choose a pattern. Use the Read tool on the "
            "file path to load the full contract (structure, recognition conditions, anti-patterns) "
            "before applying a pattern.",
            "",
        ]
        for category in sorted(by_category):
            lines.append(f"## {category.capitalize()}")
            lines.append("")
            for name, desc, path in by_category[category]:
                suffix = f" — {desc}" if desc else ""
                lines.append(f"- **{name}**{suffix}")
                lines.append(f"  - path: `{path}`")
            lines.append("")

        return "\n".join(lines).rstrip() + "\n"
