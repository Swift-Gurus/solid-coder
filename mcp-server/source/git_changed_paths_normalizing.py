"""Defines normalization of categorized Git paths."""

from typing import Protocol

from source.git_changed_paths import GitChangedPaths


"""
solid-name: GitChangedPathsNormalizing
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for normalizing overlapping categorized Git path identities.
"""
class GitChangedPathsNormalizing(Protocol):
    def normalize(self, paths: GitChangedPaths) -> GitChangedPaths: ...
