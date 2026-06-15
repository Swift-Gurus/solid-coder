"""
solid-description: Submits findings and returns results as a string.
solid-category: service
solid-tags: [hook, llm]
"""

from typing import Optional, Protocol

from llama.json_serializer import JsonSerializing, JsonSerializer


class BatchFindingsHandling(Protocol):
    def submit_batch_findings(self, output_dir: str, submissions: dict) -> dict: ...


class FindingsSubmitting(Protocol):
    def submit(self, output_dir: str, submissions: dict) -> str: ...


class GatewayFindingsSubmitter:
    """Adapts a BatchFindingsHandling handler to FindingsSubmitting, serializing the result."""

    def __init__(
        self,
        handler: BatchFindingsHandling,
        serializer: Optional[JsonSerializing] = None,
    ) -> None:
        self._handler = handler
        self._serialize: JsonSerializing = serializer or JsonSerializer()

    def submit(self, output_dir: str, submissions: dict) -> str:
        result = self._handler.submit_batch_findings(output_dir, submissions)
        return self._serialize.serialize(result)
