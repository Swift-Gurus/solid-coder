"""Composes deterministic Git change collection."""

from harness.process_execution_runner_adapter import ProcessExecutionRunnerAdapter
from hook_utils import SubprocessAdapter
from source.collect_changes_operation import CollectChangesOperation
from source.diff_hunk_destination_decoder import DiffHunkDestinationDecoder
from source.git_added_line_ranges_reader import GitAddedLineRangesReader
from source.git_changed_paths_reader import GitChangedPathsReader
from source.git_query_executor import GitQueryExecutor
from source.git_rename_records_parser import GitRenameRecordsParser
from source.nul_delimited_paths_parser import NulDelimitedPathsParser
from source.readable_whole_file_range_resolver import (
    ReadableWholeFileRangeResolver,
)
from source.source_line_ranges_coalescer import SourceLineRangesCoalescer
from source.source_operation_error_factory import SourceOperationErrorFactory
from source.rename_precedence_changed_paths_normalizer import (
    RenamePrecedenceChangedPathsNormalizer,
)
from source.unified_diff_added_line_ranges_parser import (
    UnifiedDiffAddedLineRangesParser,
)
from utils.prompt_builder import PlainTextFileReader


"""
solid-name: CollectChangesOperationFactory
solid-category: factory
solid-spec: [SPEC-040]
solid-description: Composes the typed collaborators required for deterministic Git change collection.
"""
class CollectChangesOperationFactory:
    def make(self) -> CollectChangesOperation:
        git = GitQueryExecutor(
            ProcessExecutionRunnerAdapter(SubprocessAdapter())
        )
        return CollectChangesOperation(
            paths=GitChangedPathsReader(
                git=git,
                paths_parser=NulDelimitedPathsParser(),
                renames_parser=GitRenameRecordsParser(
                    SourceOperationErrorFactory()
                ),
                normalizer=RenamePrecedenceChangedPathsNormalizer(),
            ),
            added_ranges=GitAddedLineRangesReader(
                git=git,
                parser=UnifiedDiffAddedLineRangesParser(
                    destination_decoder=DiffHunkDestinationDecoder(),
                    ranges=SourceLineRangesCoalescer(),
                ),
            ),
            whole_file_range=ReadableWholeFileRangeResolver(
                PlainTextFileReader()
            ),
        )
