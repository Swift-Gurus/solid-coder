"""Defines the opaque MCP batch-submission boundary."""

from typing import Protocol


"""
solid-name: McpBatchSubmissionHandling
solid-category: abstraction
solid-description: Contract for accepting opaque MCP batch input and returning a model-facing submission response.
"""
class McpBatchSubmissionHandling(Protocol):
    def submit_batch_findings(
        self,
        output_dir: str,
        raw_submissions: object,
    ) -> dict: ...
