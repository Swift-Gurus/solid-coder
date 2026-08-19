"""Defines file-backed source resolution."""

from typing import Protocol

from source.file_analysis_source import FileAnalysisSource
from source.resolved_analysis_source import ResolvedAnalysisSource


"""
solid-name: FileAnalysisSourceResolving
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for resolving accessible file-backed analysis content.
"""
class FileAnalysisSourceResolving(Protocol):
    def resolve(self, source: FileAnalysisSource) -> ResolvedAnalysisSource: ...
