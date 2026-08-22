"""Executes filtered typed source search from codebase-search arguments."""

from typing import Optional

from search.codebase_search_executing import CodebaseSearchExecuting
from search.codebase_search_execution import CodebaseSearchExecution
from search.codebase_search_input_building import CodebaseSearchInputBuilding
from search.source_search_output_filtering import SourceSearchOutputFiltering
from source.source_search_operation_factory import SourceSearchOperationFactory
from source.search_target_granularity import SearchTargetGranularity


"""
solid-name: CodebaseSearchExecutor
solid-category: service
solid-spec: [SPEC-040]
solid-description: Executes validated codebase source searches and applies candidate eligibility policy.
"""
class CodebaseSearchExecutor(CodebaseSearchExecuting):

    def __init__(
        self,
        input_builder: CodebaseSearchInputBuilding,
        operation_factory: SourceSearchOperationFactory,
        output_filter: SourceSearchOutputFiltering,
    ) -> None:
        self._input_builder = input_builder
        self._operation_factory = operation_factory
        self._output_filter = output_filter

    def execute(
        self,
        sources_dir: Optional[str],
        plan_path: Optional[str],
        tags: Optional[list[str]],
        spec_numbers: Optional[list[str]],
        min_matches: int,
    ) -> CodebaseSearchExecution:
        resolution = self._input_builder.build(
            sources_dir,
            plan_path,
            tags,
            spec_numbers,
            min_matches,
        )
        operation = self._operation_factory.make(
            lambda: resolution.project_root,
            SearchTargetGranularity.FILE,
        )
        output = operation.execute(resolution.operation_input)
        return CodebaseSearchExecution(
            output=self._output_filter.filter(
                output,
                resolution.minimum_matches,
            ),
            project_root=resolution.project_root,
        )
