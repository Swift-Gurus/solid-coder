"""Formats batch findings outcomes for MCP clients."""

from findings.batch_coverage_failure import BatchCoverageFailure
from findings.batch_persistence_result import BatchPersistenceResult
from findings.batch_submission_parse_failure import BatchSubmissionParseFailure
from findings.batch_submission_response_formatting import BatchSubmissionResponseFormatting
from findings.violation_reader import ViolationReading
from findings.violation_response_formatting import ViolationResponseFormatting


"""
solid-name: McpBatchSubmissionResponseFormatter
solid-category: boundary-adapter
solid-description: Renders typed batch findings outcomes and severe violations as model-facing MCP responses.
"""
class McpBatchSubmissionResponseFormatter(BatchSubmissionResponseFormatting):
    def __init__(
        self,
        violation_reader: ViolationReading,
        violation_formatter: ViolationResponseFormatting,
    ) -> None:
        self._violation_reader = violation_reader
        self._violation_formatter = violation_formatter

    def format_coverage_failure(self, failure: BatchCoverageFailure) -> dict:
        skipped = list(failure.principle_labels)
        expected = list(failure.expected_units)
        units = ", ".join(failure.expected_units)
        return {
            "error": "incomplete_submission",
            "detail": (
                f"Principles {skipped} submitted no units for a file containing "
                f"[{units}]. Every active SOLID principle must analyze every code "
                f"unit — submitting empty units is detectable and causes an expensive "
                f"re-run. Re-submit with complete analysis for {skipped}."
            ),
            "principles_with_no_units": skipped,
            "expected_units": expected,
        }

    def format_parse_failure(self, failure: BatchSubmissionParseFailure) -> dict:
        return {
            "error": failure.message,
            "failed_at": failure.principle_label,
        }

    def format_persistence_failure(self, failure: BatchPersistenceResult) -> dict:
        return {
            "error": failure.error_message,
            "failed_at": failure.failed_principle_label,
        }

    def format_success(self, output_dir: str) -> dict:
        violations = self._violation_reader.read_violations(output_dir)
        return self._violation_formatter.format(violations, output_dir)
