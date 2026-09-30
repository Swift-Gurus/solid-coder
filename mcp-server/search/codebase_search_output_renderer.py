"""Renders typed source-search results for LLM inspection."""

from pathlib import Path

from search.codebase_search_output_rendering import CodebaseSearchOutputRendering
from source.source_search_results import SourceSearchResults


"""
solid-name: CodebaseSearchOutputRenderer
solid-category: presenter
solid-spec: [SPEC-040, SPEC-056]
solid-description: Presents stable candidate IDs, reusable source units, descriptions, and absolute inspection paths.
"""
class CodebaseSearchOutputRenderer(CodebaseSearchOutputRendering):
    def render(
        self,
        output: SourceSearchResults,
        project_root: Path,
    ) -> str:
        if not output.candidates:
            return (
                f"No files matched in {project_root} "
                f"({output.files_scanned} files scanned)."
            )

        lines = ["Here is what we found:"]
        for index, candidate in enumerate(output.candidates, start=1):
            lines.extend([
                "",
                f"candidate_id: candidate-{index}",
                f"unit: {candidate.unit}",
                f"description: {candidate.description}",
                f"path: {candidate.path}",
            ])
        return "\n".join(lines)
