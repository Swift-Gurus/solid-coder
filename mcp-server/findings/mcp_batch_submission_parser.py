"""Coordinates parsing of MCP findings batch submissions."""

from typing import cast

from findings.batch_submission import BatchSubmission
from findings.batch_submission_building import BatchSubmissionBuilding
from findings.batch_submission_parse_failure import BatchSubmissionParseFailure
from findings.batch_submission_parse_result import BatchSubmissionParseResult
from findings.batch_submission_parsing import BatchSubmissionParsing
from findings.batch_submission_payload_validating import BatchSubmissionPayloadValidating
from findings.partial_output_validator import PartialOutputValidating
from findings.principle_submission import PrincipleSubmission


"""
solid-name: McpBatchSubmissionParser
solid-category: boundary-adapter
solid-description: Parses structurally valid ordered batch review submissions and reports the first rejected principle.
"""
class McpBatchSubmissionParser(BatchSubmissionParsing):
    def __init__(
        self,
        payload_validator: BatchSubmissionPayloadValidating,
        output_validator: PartialOutputValidating,
        builder: BatchSubmissionBuilding,
    ) -> None:
        self._payload_validator = payload_validator
        self._output_validator = output_validator
        self._builder = builder

    def parse(self, raw_submissions: object) -> BatchSubmissionParseResult:
        if not self._payload_validator.is_valid(raw_submissions):
            return self._failure(
                label="batch",
                message="submissions must contain string labels and object payloads",
            )

        accepted: tuple[PrincipleSubmission, ...] = ()
        for label, raw_output in cast(dict, raw_submissions).items():
            validation_error = self._output_validator.validate_output(raw_output)
            if validation_error is not None:
                return self._failure(
                    label=label,
                    message=str(validation_error.get("error", "invalid submission")),
                    accepted=accepted,
                )

            accepted += self._builder.build({label: raw_output}).principles

        return BatchSubmissionParseResult(
            submission=BatchSubmission(principles=accepted),
        )

    def _failure(
        self,
        label: str,
        message: str,
        accepted: tuple[PrincipleSubmission, ...] = (),
    ) -> BatchSubmissionParseResult:
        return BatchSubmissionParseResult(
            submission=BatchSubmission(principles=accepted),
            failure=BatchSubmissionParseFailure(
                principle_label=label,
                message=message,
            ),
        )
