"""Defines a renamed source-file change."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

from source.source_change_kind import SourceChangeKind
from source.source_line_range import SourceLineRange


"""
solid-name: RenamedSourceFileChange
solid-category: model
solid-spec: [SPEC-040]
solid-description: Represents a renamed source-file change with previous and destination paths.
"""
class RenamedSourceFileChange(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal[SourceChangeKind.RENAMED] = SourceChangeKind.RENAMED
    previous_path: str
    path: str
    added_ranges: list[SourceLineRange]
