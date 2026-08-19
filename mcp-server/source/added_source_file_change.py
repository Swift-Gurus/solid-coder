"""Defines an added source-file change."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

from source.source_change_kind import SourceChangeKind
from source.source_line_range import SourceLineRange


"""
solid-name: AddedSourceFileChange
solid-category: model
solid-spec: [SPEC-040]
solid-description: Represents an added source file and its complete destination-coordinate line ranges.
"""
class AddedSourceFileChange(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal[SourceChangeKind.ADDED] = SourceChangeKind.ADDED
    path: str
    added_ranges: list[SourceLineRange]
