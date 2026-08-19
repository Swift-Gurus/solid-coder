"""Reads categorized changed paths from Git."""

from pathlib import Path

from source.git_changed_paths import GitChangedPaths
from source.git_changed_paths_normalizing import GitChangedPathsNormalizing
from source.git_changed_paths_reading import GitChangedPathsReading
from source.git_process_execution import GitProcessExecution
from source.git_querying import GitQuerying
from source.git_rename_records_parsing import GitRenameRecordsParsing
from source.nul_delimited_paths_parsing import NulDelimitedPathsParsing


"""
solid-name: GitChangedPathsReader
solid-category: service
solid-spec: [SPEC-040]
solid-description: Reads staged, unstaged, untracked, deleted, and renamed project-relative paths from Git.
"""
class GitChangedPathsReader(GitChangedPathsReading):
    def __init__(
        self,
        git: GitQuerying,
        paths_parser: NulDelimitedPathsParsing,
        renames_parser: GitRenameRecordsParsing,
        normalizer: GitChangedPathsNormalizing,
    ) -> None:
        self._git = git
        self._paths_parser = paths_parser
        self._renames_parser = renames_parser
        self._normalizer = normalizer

    def read(self, project_root: Path) -> GitChangedPaths:
        return self._normalizer.normalize(GitChangedPaths(
            tracked_added=self._paths(
                project_root,
                ["diff", "--name-only", "-z", "--diff-filter=A", "HEAD"],
                "collecting tracked additions",
            ),
            untracked=self._paths(
                project_root,
                ["ls-files", "--others", "--exclude-standard", "-z"],
                "collecting untracked files",
            ),
            modified=self._paths(
                project_root,
                ["diff", "--name-only", "-z", "--diff-filter=M", "HEAD"],
                "collecting modified files",
            ),
            deleted=self._paths(
                project_root,
                ["diff", "--name-only", "-z", "--diff-filter=D", "HEAD"],
                "collecting deleted files",
            ),
            renamed=self._renames_parser.parse(
                self._git.query(
                    project_root,
                    GitProcessExecution(
                        [
                            "diff",
                            "--name-status",
                            "-z",
                            "--find-renames",
                            "--diff-filter=R",
                            "HEAD",
                        ]
                    ),
                    "collecting renamed files",
                )
            ),
        ))

    def _paths(
        self,
        project_root: Path,
        arguments: list[str],
        purpose: str,
    ) -> list[str]:
        return self._paths_parser.parse(
            self._git.query(
                project_root,
                GitProcessExecution(arguments),
                purpose,
            )
        )
