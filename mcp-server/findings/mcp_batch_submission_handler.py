"""Adapts opaque MCP batch input to typed submission handling."""

from findings.batch_submission_handling import BatchSubmissionHandling
from findings.batch_submission_parsing import BatchSubmissionParsing
from findings.mcp_batch_submission_handling import McpBatchSubmissionHandling


"""
solid-name: McpBatchSubmissionHandler
solid-category: boundary-adapter
solid-description: Translates untyped batch submissions into validated model-facing outcomes.
"""
class McpBatchSubmissionHandler(McpBatchSubmissionHandling):
    def __init__(
        self,
        parser: BatchSubmissionParsing,
        handler: BatchSubmissionHandling,
    ) -> None:
        self._parser = parser
        self._handler = handler

    def submit_batch_findings(
        self,
        output_dir: str,
        raw_submissions: object,
    ) -> dict:
        return self._handler.submit_batch(
            output_dir,
            self._parser.parse(raw_submissions),
        )
