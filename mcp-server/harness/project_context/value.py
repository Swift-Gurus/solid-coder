"""Defines an immutable resolved project-directory value."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict


"""
solid-name: ProjectDirectory
solid-category: model
solid-spec: [SPEC-049]
solid-description: Carries one resolved project directory through typed service boundaries.
"""
class ProjectDirectory(BaseModel):
    model_config = ConfigDict(frozen=True)

    path: Path

    def read(self) -> Path:
        return self.path
