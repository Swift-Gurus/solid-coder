"""Defines the typed input for Git change collection."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict, field_validator


"""
solid-name: CollectChangesInput
solid-category: model
solid-spec: [SPEC-040]
solid-description: Identifies the project whose Git working-tree changes must be collected.
"""
class CollectChangesInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    project_root: Path

    @field_validator("project_root")
    @classmethod
    def canonicalize_project_root(cls, value: Path) -> Path:
        return value.resolve()
