"""Decodes compiler context supplied by the active semantic session."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


"""
solid-name: SourceKitCompilerOptions
solid-category: model
solid-spec: [SPEC-064]
solid-description: Carries compiler arguments and their working directory from the semantic provider without guessing project build settings.
"""
class SourceKitCompilerOptions(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True, populate_by_name=True)

    compiler_arguments: list[str] = Field(validation_alias="compilerArguments", min_length=1)
    working_directory: Path | None = Field(default=None, validation_alias="workingDirectory")
    kind: Literal["normal", "fallback"]
