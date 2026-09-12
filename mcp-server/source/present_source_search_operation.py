"""Presents typed source-search results for a workflow agent step."""

from harness.project_context import ProjectDirectoryReading
from search.codebase_search_output_rendering import CodebaseSearchOutputRendering
from source.source_search_output import SourceSearchOutput
from source.source_search_presentation import SourceSearchPresentation


"""
solid-name: PresentSourceSearchOperation
solid-category: service
solid-spec: [SPEC-039, SPEC-040]
solid-description: Adapts typed source-search results into the shared readable model-facing presentation.
"""
class PresentSourceSearchOperation:
    def __init__(
        self,
        renderer: CodebaseSearchOutputRendering,
        project_directory: ProjectDirectoryReading,
    ) -> None:
        self._renderer = renderer
        self._project_directory = project_directory

    def execute(
        self,
        operation_input: SourceSearchOutput,
    ) -> SourceSearchPresentation:
        return SourceSearchPresentation(
            text=self._renderer.render(
                operation_input,
                self._project_directory.read().resolve(),
            )
        )
