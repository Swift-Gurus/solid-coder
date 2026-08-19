"""Defines an in-memory source-analysis request variant."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Optional, TypeVar

from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from source.analysis_source_visitor import AnalysisSourceVisitor

VisitResult = TypeVar("VisitResult")


"""
solid-name: TextAnalysisSource
solid-category: model
solid-spec: [SPEC-040]
solid-description: Carries source text and optional identity hints for deterministic analysis.
"""
class TextAnalysisSource(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["text"] = "text"
    text: str
    virtual_path: Optional[str] = None
    language_hint: Optional[str] = None

    def accept(
        self,
        visitor: AnalysisSourceVisitor[VisitResult],
    ) -> VisitResult:
        return visitor.visit_text(self)
