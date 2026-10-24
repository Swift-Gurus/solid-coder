"""Composes production codebase source-search execution."""

from gate_logger import GateLogger
from harness.json_loading import JsonLoader
from harness.ordered_string_collector import OrderedStringCollector
from harness.project_context import ProjectDirectoryReading
from harness.pydantic_model_decoder import PydanticModelDecoder
from health.config.hc_config_core import find_repository_root
from hook_utils import _resolve_project_root
from scoring.yaml_config_file_loader import YamlConfigFileLoader
from source.exact_source_tokens_resolver_factory import (
    ExactSourceTokensResolverFactory,
)
from source.repository_target_resolver import RepositoryTargetResolver
from source.source_search_operation_factory import SourceSearchOperationFactory
from utils.debug_logger import DebugLogger

from search.codebase_search_executor import CodebaseSearchExecutor
from search.codebase_search_input_builder import CodebaseSearchInputBuilder
from search.codebase_search_query_kind import CodebaseSearchQueryKind
from search.codebase_search_terms_resolver import CodebaseSearchTermsResolver
from search.search_plan_document import SearchPlanDocument
from search.source_search_output_filter import SourceSearchOutputFilter

"""
solid-name: CodebaseSearchExecutorFactory
solid-category: factory
solid-spec: [SPEC-040]
solid-description: Provides production codebase source-search executors.
"""


class CodebaseSearchExecutorFactory:
    def make(
        self, project_directory: ProjectDirectoryReading | None = None
    ) -> CodebaseSearchExecutor:
        return CodebaseSearchExecutor(
            input_builder=CodebaseSearchInputBuilder(
                current_directory=(
                    project_directory.read
                    if project_directory is not None
                    else _resolve_project_root
                ),
                targets=RepositoryTargetResolver(find_repository_root),
                terms=CodebaseSearchTermsResolver(
                    plan_loader=YamlConfigFileLoader(
                        loader=JsonLoader(), logger=GateLogger(DebugLogger())
                    ),
                    plan_decoder=PydanticModelDecoder(
                        model_type=SearchPlanDocument,
                    ),
                    tokens=ExactSourceTokensResolverFactory().make(),
                    strings=OrderedStringCollector(),
                ),
                query_kinds=CodebaseSearchQueryKind,
            ),
            operation_factory=SourceSearchOperationFactory(),
            output_filter=SourceSearchOutputFilter(),
        )
