"""Builds DRY-search enforcement services."""

from findings.batch_submission_handling import BatchSubmissionHandling
from findings.batch_submission_decorating import BatchSubmissionDecorating
from health.dry_search_coordinator import DrySearchCoordinator
from health.dry_search_enforcing_batch_findings_submitter import (
    DrySearchEnforcingBatchFindingsSubmitter,
)
from health.file_dry_search_completion_store import FileDrySearchCompletionStore
from harness.path_builder import PathBuilder
from harness.path_checking import PathChecker
from harness.posix_atomic_file_writer import POSIXAtomicFileWriter
from search.regex_search_term_extractor import RegexSearchTermExtractor
from search.search_terms_resolver import SearchTermsResolver
from search.tag_codebase_searching import TagCodebaseSearching


"""
solid-name: DrySearchServiceFactory
solid-category: factory
solid-description: Builds production services for validated DRY searches and submission enforcement.
"""
class DrySearchServiceFactory(BatchSubmissionDecorating):
    def make_search(self, search: TagCodebaseSearching) -> DrySearchCoordinator:
        return DrySearchCoordinator(
            search=search,
            terms=SearchTermsResolver(RegexSearchTermExtractor()),
            completion=self.make_completion_store(),
        )

    def make_submission(
        self,
        submission: BatchSubmissionHandling,
    ) -> DrySearchEnforcingBatchFindingsSubmitter:
        return DrySearchEnforcingBatchFindingsSubmitter(
            submission=submission,
            completion=self.make_completion_store(),
        )

    def make_completion_store(self) -> FileDrySearchCompletionStore:
        return FileDrySearchCompletionStore(
            path_builder=PathBuilder(),
            path_checker=PathChecker(),
            marker_writer=POSIXAtomicFileWriter(),
        )
