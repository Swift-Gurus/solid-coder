"""Collects deterministic typed Git working-tree changes."""

from source.added_line_ranges_reading import AddedLineRangesReading
from source.added_source_file_change import AddedSourceFileChange
from source.collect_changes_input import CollectChangesInput
from source.collect_changes_output import CollectChangesOutput
from source.deleted_source_file_change import DeletedSourceFileChange
from source.git_changed_paths_reading import GitChangedPathsReading
from source.modified_source_file_change import ModifiedSourceFileChange
from source.renamed_source_file_change import RenamedSourceFileChange
from source.source_file_change import SourceFileChange
from source.whole_file_range_resolving import WholeFileRangeResolving


"""
solid-name: CollectChangesOperation
solid-category: service
solid-spec: [SPEC-040]
solid-description: Collects ordered typed source-file changes from a Git working tree without mutation.
"""
class CollectChangesOperation:
    def __init__(
        self,
        paths: GitChangedPathsReading,
        added_ranges: AddedLineRangesReading,
        whole_file_range: WholeFileRangeResolving,
    ) -> None:
        self._paths = paths
        self._added_ranges = added_ranges
        self._whole_file_range = whole_file_range

    def execute(
        self,
        operation_input: CollectChangesInput,
    ) -> CollectChangesOutput:
        project_root = operation_input.project_root
        paths = self._paths.read(project_root)
        changes: list[SourceFileChange] = [
            *[
                AddedSourceFileChange(
                    path=path,
                    added_ranges=self._added_ranges.read(project_root, [path]),
                )
                for path in paths.tracked_added
            ],
            *[
                AddedSourceFileChange(
                    path=path,
                    added_ranges=self._whole_file_range.resolve(
                        project_root / path
                    ),
                )
                for path in paths.untracked
            ],
            *[
                ModifiedSourceFileChange(
                    path=path,
                    added_ranges=self._added_ranges.read(project_root, [path]),
                )
                for path in paths.modified
            ],
            *[
                DeletedSourceFileChange(path=path)
                for path in paths.deleted
            ],
            *[
                RenamedSourceFileChange(
                    previous_path=rename.previous_path,
                    path=rename.path,
                    added_ranges=self._added_ranges.read(
                        project_root,
                        [rename.previous_path, rename.path],
                    ),
                )
                for rename in paths.renamed
            ],
        ]
        return CollectChangesOutput(
            files=sorted(changes, key=lambda change: change.path)
        )
