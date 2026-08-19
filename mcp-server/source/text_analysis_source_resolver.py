"""Resolves in-memory text-backed source content."""

from gate.file_extension_extracting import FileExtensionExtracting
from harness.path_canonicalizing import PathCanonicalizing
from source.resolved_analysis_source import ResolvedAnalysisSource
from source.text_analysis_source import TextAnalysisSource
from source.text_analysis_source_resolving import TextAnalysisSourceResolving


"""
solid-name: TextAnalysisSourceResolver
solid-category: service
solid-spec: [SPEC-040]
solid-description: Normalizes one in-memory text-backed analysis source and its optional hints.
"""
class TextAnalysisSourceResolver(TextAnalysisSourceResolving):
    def __init__(
        self,
        path_canonicalizer: PathCanonicalizing,
        extension_extractor: FileExtensionExtracting,
    ) -> None:
        self._path_canonicalizer = path_canonicalizer
        self._extension_extractor = extension_extractor

    def resolve(
        self,
        source: TextAnalysisSource,
    ) -> ResolvedAnalysisSource:
        identity = (
            self._path_canonicalizer.canonicalize(source.virtual_path)
            if source.virtual_path
            else "<buffer>"
        )
        file_extension = (
            source.file_extension.strip().lower()
            if source.file_extension
            else self._extension_extractor.suffix_of(identity).lower()
        )
        return ResolvedAnalysisSource(
            identity=identity,
            file_extension=file_extension,
            text=source.text,
        )
