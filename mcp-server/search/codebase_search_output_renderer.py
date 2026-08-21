"""Renders typed source-search results for LLM inspection."""

from pathlib import Path

from search.codebase_search_output_rendering import CodebaseSearchOutputRendering
from source.source_search_output import SourceSearchOutput


"""
solid-name: CodebaseSearchOutputRenderer
solid-category: presenter
solid-spec: [SPEC-040]
solid-description: Presents reusable source units with descriptions and absolute inspection paths.
"""
class CodebaseSearchOutputRenderer(CodebaseSearchOutputRendering):
    def render(
        self,
        output: SourceSearchOutput,
        project_root: Path,
    ) -> str:
        if not output.candidates:
            return (
                f"No files matched in {project_root} "
                f"({output.files_scanned} files scanned)."
            )

        lines = ["Here is what we found:"]
        for candidate in output.candidates:
            lines.extend([
                "",
                f"unit: {candidate.unit}",
                f"description: {candidate.description}",
                f"path: {candidate.path}",
            ])
        return "\n".join(lines)
