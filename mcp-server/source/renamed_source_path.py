"""Defines previous and destination identities for one Git rename."""

from dataclasses import dataclass


"""
solid-name: RenamedSourcePath
solid-category: model
solid-spec: [SPEC-040]
solid-description: Represents previous and destination project-relative paths for a Git rename.
"""
@dataclass(frozen=True)
class RenamedSourcePath:
    previous_path: str
    path: str
