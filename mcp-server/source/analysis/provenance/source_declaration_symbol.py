"""Carries a semantically resolved declaration location."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


"""
solid-name: SourceDeclarationSymbol
solid-category: model
solid-spec: [SPEC-064]
solid-description: Identifies a verified source declaration independently from its repository ownership.
"""
class SourceDeclarationSymbol(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["declaration"] = "declaration"
    symbol_id: str = Field(min_length=1)
    declaration_path: Path

    @field_validator("declaration_path")
    @classmethod
    def validate_absolute_path(cls, path: Path) -> Path:
        if not path.is_absolute():
            raise ValueError("A resolved declaration requires an absolute path.")
        return path
