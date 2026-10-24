"""Composes sealed file and text source resolution."""

from pathlib import Path

from harness.path_builder import PathBuilder
from harness.path_canonicalizer import PathCanonicalizer
from harness.project_context import ProjectDirectoryReading
from health.config.hc_config_core import find_repository_root
from hook_utils import _resolve_project_root
from hooks.pathlib_extractor import PathlibExtractor
from source.analysis_source_dispatch_visitor import AnalysisSourceDispatchVisitor
from source.analysis_source_resolver import AnalysisSourceResolver
from source.file_analysis_source_resolver import FileAnalysisSourceResolver
from source.repository_target_resolver import RepositoryTargetResolver
from source.text_analysis_source_resolver import TextAnalysisSourceResolver
from utils.prompt_builder import PlainTextFileReader

"""
solid-name: AnalysisSourceResolverFactory
solid-category: factory
solid-spec: [SPEC-040]
solid-description: Provides normalized immutable source resolution for file-backed and in-memory analysis inputs.
"""


class AnalysisSourceResolverFactory:
    def make(
        self, project_directory: ProjectDirectoryReading | None = None
    ) -> AnalysisSourceResolver:
        extension_extractor = PathlibExtractor(lambda path: Path(path).suffix.lower())
        return AnalysisSourceResolver(
            AnalysisSourceDispatchVisitor(
                file_resolver=FileAnalysisSourceResolver(
                    reader=PlainTextFileReader(),
                    extension_extractor=extension_extractor,
                    targets=RepositoryTargetResolver(find_repository_root),
                    current_directory=(
                        project_directory.read
                        if project_directory is not None
                        else _resolve_project_root
                    ),
                ),
                text_resolver=TextAnalysisSourceResolver(
                    path_canonicalizer=PathCanonicalizer(PathBuilder()),
                    extension_extractor=extension_extractor,
                ),
            )
        )
