"""Composes production codebase source-search execution."""

from pathlib import Path

from harness.json_loading import JsonLoader
from harness.ordered_string_collector import OrderedStringCollector
from harness.pydantic_model_decoder import PydanticModelDecoder
from scoring.yaml_config_file_loader import YamlConfigFileLoader
from search.codebase_search_executor import CodebaseSearchExecutor
from search.codebase_search_input_builder import CodebaseSearchInputBuilder
from search.codebase_search_query_kind import CodebaseSearchQueryKind
from search.codebase_search_terms_resolver import CodebaseSearchTermsResolver
from search.search_plan_document import SearchPlanDocument
from search.source_search_output_filter import SourceSearchOutputFilter
from source.exact_source_tokens_resolver_factory import (
    ExactSourceTokensResolverFactory,
)
from source.source_search_operation_factory import SourceSearchOperationFactory


"""
solid-name: CodebaseSearchExecutorFactory
solid-category: factory
solid-spec: [SPEC-040]
solid-description: Provides production codebase source-search executors.
"""
class CodebaseSearchExecutorFactory:
    def make(self) -> CodebaseSearchExecutor:
        return CodebaseSearchExecutor(
            input_builder=CodebaseSearchInputBuilder(
                current_directory=Path.cwd,
                terms=CodebaseSearchTermsResolver(
                    plan_loader=YamlConfigFileLoader(loader=JsonLoader()),
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
