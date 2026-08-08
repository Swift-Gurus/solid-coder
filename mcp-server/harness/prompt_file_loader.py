"""Loads required prompt file content."""

from __future__ import annotations

from pathlib import Path

from harness.flow_validation_error_creating import FlowValidationErrorCreating
from utils.prompt_builder import TextFileReading


"""
solid-name: PromptFileLoader
solid-category: service
solid-spec: [SPEC-027]
solid-description: Loads required prompt text and reports an actionable missing-resource failure.
"""
class PromptFileLoader:

    def __init__(
        self,
        reader: TextFileReading,
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._reader = reader
        self._error_factory = error_factory

    def load(self, path: Path, step_id: str, reference: str) -> str:
        content = self._reader.read(path)
        if content is None:
            raise self._error_factory.create(
                f"Step '{step_id}' prompt_file not found: '{reference}'"
            )
        return content
