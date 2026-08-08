"""Validates external MCP batch-submission payloads."""

from findings.batch_submission_payload_validating import BatchSubmissionPayloadValidating


"""
solid-name: McpBatchSubmissionPayloadValidator
solid-category: boundary-adapter
solid-description: Verifies that an external batch review request has ordered string labels and object payloads.
"""
class McpBatchSubmissionPayloadValidator(BatchSubmissionPayloadValidating):
    def is_valid(self, raw_submissions: object) -> bool:
        if not isinstance(raw_submissions, dict):
            return False
        return all(
            isinstance(label, str)
            and isinstance(raw_output, dict)
            for label, raw_output in raw_submissions.items()
        )
