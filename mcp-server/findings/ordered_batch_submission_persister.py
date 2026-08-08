"""Persists immutable principle submissions in batch order."""

from findings.batch_persistence_result import BatchPersistenceResult
from findings.batch_submission import BatchSubmission
from findings.batch_submission_persisting import BatchSubmissionPersisting
from findings.principle_submission_submitting import PrincipleSubmissionSubmitting
from harness.path_building import PathBuilding


"""
solid-name: OrderedBatchSubmissionPersister
solid-category: service
solid-description: Persists principle reviews sequentially and stops at the first labelled submission failure.
"""
class OrderedBatchSubmissionPersister(BatchSubmissionPersisting):
    def __init__(
        self,
        submission_submitter: PrincipleSubmissionSubmitting,
        path_builder: PathBuilding,
    ) -> None:
        self._submission_submitter = submission_submitter
        self._path_builder = path_builder

    def persist(
        self,
        output_dir: str,
        submission: BatchSubmission,
    ) -> BatchPersistenceResult:
        for principle in submission.principles:
            principle_directory = self._path_builder.build(output_dir, principle.label)
            output_path = self._path_builder.build(
                principle_directory,
                "review-output.json",
            )
            result = self._submission_submitter.submit(principle, output_path)
            if not result.succeeded:
                return BatchPersistenceResult(
                    failed_principle_label=principle.label,
                    error_message=result.error_message,
                )
        return BatchPersistenceResult()
