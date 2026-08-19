"""Defines typed path identities reported by Git."""

from dataclasses import dataclass, field

from source.renamed_source_path import RenamedSourcePath


"""
solid-name: GitChangedPaths
solid-category: model
solid-spec: [SPEC-040]
solid-description: Carries categorized project-relative paths reported by Git working-tree queries.
"""
@dataclass(frozen=True)
class GitChangedPaths:
    tracked_added: list[str] = field(default_factory=list)
    untracked: list[str] = field(default_factory=list)
    modified: list[str] = field(default_factory=list)
    deleted: list[str] = field(default_factory=list)
    renamed: list[RenamedSourcePath] = field(default_factory=list)
