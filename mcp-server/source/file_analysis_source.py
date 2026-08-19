"""Defines a file-backed source-analysis request variant."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Literal, TypeVar

from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from source.analysis_source_visitor import AnalysisSourceVisitor

VisitResult = TypeVar("VisitResult")


"""
solid-name: FileAnalysisSource
solid-category: model
solid-spec: [SPEC-040]
solid-description: Identifies one accessible source file for deterministic analysis.
"""
class FileAnalysisSource(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["file"] = "file"
    path: Path

    def accept(
        self,
        visitor: AnalysisSourceVisitor[VisitResult],
    ) -> VisitResult:
        return visitor.visit_file(self)
