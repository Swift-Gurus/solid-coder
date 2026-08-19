"""Defines polymorphic dispatch across sealed analysis-source variants."""

from __future__ import annotations

from typing import Generic, Protocol, TypeVar

from source.file_analysis_source import FileAnalysisSource
from source.text_analysis_source import TextAnalysisSource

VisitResult = TypeVar("VisitResult")


"""
solid-name: AnalysisSourceVisitor
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for source-specific behavior across sealed file and text analysis variants.
"""
class AnalysisSourceVisitor(Protocol, Generic[VisitResult]):
    def visit_file(self, source: FileAnalysisSource) -> VisitResult: ...

    def visit_text(self, source: TextAnalysisSource) -> VisitResult: ...
