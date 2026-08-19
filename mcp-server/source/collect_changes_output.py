"""Defines the typed result of Git change collection."""

from pydantic import BaseModel, ConfigDict

from source.source_file_change import SourceFileChange


"""
solid-name: CollectChangesOutput
solid-category: model
solid-spec: [SPEC-040]
solid-description: Carries ordered typed source-file changes from one Git working tree.
"""
class CollectChangesOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    files: list[SourceFileChange]
