"""Defines a modified source-file change."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

from source.source_change_kind import SourceChangeKind
from source.source_line_range import SourceLineRange


"""
solid-name: ModifiedSourceFileChange
solid-category: model
solid-spec: [SPEC-040]
solid-description: Represents a modified source file and its destination-coordinate added line ranges.
"""
class ModifiedSourceFileChange(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal[SourceChangeKind.MODIFIED] = SourceChangeKind.MODIFIED
    path: str
    added_ranges: list[SourceLineRange]
