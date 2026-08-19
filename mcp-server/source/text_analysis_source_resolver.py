"""Resolves in-memory text-backed source content."""

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
    def __init__(self, path_canonicalizer: PathCanonicalizing) -> None:
        self._path_canonicalizer = path_canonicalizer

    def resolve(
        self,
        source: TextAnalysisSource,
    ) -> ResolvedAnalysisSource:
        return ResolvedAnalysisSource(
            identity=(
                self._path_canonicalizer.canonicalize(source.virtual_path)
                if source.virtual_path
                else "<buffer>"
            ),
            text=source.text,
            language_hint=source.language_hint,
        )
