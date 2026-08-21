"""Defines one completed typed codebase search."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict

from source.source_search_output import SourceSearchOutput


"""
solid-name: CodebaseSearchExecution
solid-category: model
solid-spec: [SPEC-040]
solid-description: Carries filtered source-search output and its resolved project root.
"""
class CodebaseSearchExecution(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    output: SourceSearchOutput
    project_root: Path
