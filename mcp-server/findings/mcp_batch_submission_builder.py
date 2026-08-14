"""Constructs immutable submission models from validated MCP payloads."""

from typing import cast

from pydantic import TypeAdapter

from findings.batch_submission import BatchSubmission
from findings.batch_submission_building import BatchSubmissionBuilding
from findings.mcp_batch_submission_normalizer import McpBatchSubmissionNormalizer


"""
solid-name: McpBatchSubmissionBuilder
solid-category: boundary-adapter
solid-description: Constructs the immutable submission hierarchy from a validated MCP review payload.
"""
class McpBatchSubmissionBuilder(BatchSubmissionBuilding):
    def __init__(self, legacy_serializer: object = None) -> None:
        self._normalizer = McpBatchSubmissionNormalizer()
        self._adapter = TypeAdapter(BatchSubmission)

    def build(self, validated_payload: object) -> BatchSubmission:
        return cast(
            BatchSubmission,
            self._adapter.validate_python(
                self._normalizer.normalize(validated_payload)
            ),
        )
