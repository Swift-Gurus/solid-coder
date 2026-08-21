"""Composes sealed file and text source resolution."""

from pathlib import Path

from harness.path_builder import PathBuilder
from harness.path_canonicalizer import PathCanonicalizer
from hooks.pathlib_extractor import PathlibExtractor
from source.analysis_source_dispatch_visitor import AnalysisSourceDispatchVisitor
from source.analysis_source_resolver import AnalysisSourceResolver
from source.file_analysis_source_resolver import FileAnalysisSourceResolver
from source.text_analysis_source_resolver import TextAnalysisSourceResolver
from utils.prompt_builder import PlainTextFileReader


"""
solid-name: AnalysisSourceResolverFactory
solid-category: factory
solid-spec: [SPEC-040]
solid-description: Provides normalized immutable source resolution for file-backed and in-memory analysis inputs.
"""
class AnalysisSourceResolverFactory:
    def make(self) -> AnalysisSourceResolver:
        extension_extractor = PathlibExtractor(
            lambda path: Path(path).suffix.lower()
        )
        return AnalysisSourceResolver(
            AnalysisSourceDispatchVisitor(
                file_resolver=FileAnalysisSourceResolver(
                    reader=PlainTextFileReader(),
                    extension_extractor=extension_extractor,
                ),
                text_resolver=TextAnalysisSourceResolver(
                    path_canonicalizer=PathCanonicalizer(PathBuilder()),
                    extension_extractor=extension_extractor,
                ),
            )
        )
