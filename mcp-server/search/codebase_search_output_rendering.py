"""Defines LLM-facing codebase-search output rendering."""

from pathlib import Path
from typing import Protocol

from source.source_search_output import SourceSearchOutput


"""
solid-name: CodebaseSearchOutputRendering
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for rendering typed source-search results for LLM inspection.
"""
class CodebaseSearchOutputRendering(Protocol):
    def render(
        self,
        output: SourceSearchOutput,
        project_root: Path,
    ) -> str: ...
