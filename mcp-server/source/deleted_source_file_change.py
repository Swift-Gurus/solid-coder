"""Defines a deleted source-file change."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

from source.source_change_kind import SourceChangeKind


"""
solid-name: DeletedSourceFileChange
solid-category: model
solid-spec: [SPEC-040]
solid-description: Represents a deleted source file without inventing current destination content.
"""
class DeletedSourceFileChange(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal[SourceChangeKind.DELETED] = SourceChangeKind.DELETED
    path: str
