"""Coordinates typed batch findings submission."""

from findings.batch_submission_handling import BatchSubmissionHandling
from findings.batch_submission_parse_result import BatchSubmissionParseResult
from findings.batch_submission_persisting import BatchSubmissionPersisting
from findings.batch_submission_preparing import BatchSubmissionPreparing
from findings.batch_submission_response_formatting import BatchSubmissionResponseFormatting


"""
solid-name: BatchSubmissionCoordinator
solid-category: service
solid-description: Sequences preparation, ordered persistence, and response rendering for a typed findings batch.
"""
class BatchSubmissionCoordinator(BatchSubmissionHandling):
    def __init__(
        self,
        preparer: BatchSubmissionPreparing,
        persister: BatchSubmissionPersisting,
        response_formatter: BatchSubmissionResponseFormatting,
    ) -> None:
        self._preparer = preparer
        self._persister = persister
        self._response_formatter = response_formatter

    def submit_batch(
        self,
        output_dir: str,
        parse_result: BatchSubmissionParseResult,
    ) -> dict:
        prepared = self._preparer.prepare(output_dir, parse_result.submission)
        if prepared.coverage_failure is not None:
            return self._response_formatter.format_coverage_failure(
                prepared.coverage_failure
            )

        persistence = self._persister.persist(output_dir, prepared.submission)
        if not persistence.succeeded:
            return self._response_formatter.format_persistence_failure(persistence)

        if parse_result.failure is not None:
            return self._response_formatter.format_parse_failure(parse_result.failure)

        return self._response_formatter.format_success(output_dir)
