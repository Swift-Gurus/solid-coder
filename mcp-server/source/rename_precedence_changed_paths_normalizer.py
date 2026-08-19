"""Normalizes changed paths with rename precedence."""

from source.git_changed_paths import GitChangedPaths
from source.git_changed_paths_normalizing import GitChangedPathsNormalizing


"""
solid-name: RenamePrecedenceChangedPathsNormalizer
solid-category: service
solid-spec: [SPEC-040]
solid-description: Removes added, modified, and deleted identities already represented by typed rename records.
"""
class RenamePrecedenceChangedPathsNormalizer(GitChangedPathsNormalizing):
    def normalize(self, paths: GitChangedPaths) -> GitChangedPaths:
        previous_paths = [rename.previous_path for rename in paths.renamed]
        destination_paths = [rename.path for rename in paths.renamed]
        return GitChangedPaths(
            tracked_added=[
                path
                for path in paths.tracked_added
                if path not in destination_paths
            ],
            untracked=paths.untracked,
            modified=[
                path
                for path in paths.modified
                if path not in destination_paths
            ],
            deleted=[
                path
                for path in paths.deleted
                if path not in previous_paths
            ],
            renamed=paths.renamed,
        )
