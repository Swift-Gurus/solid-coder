"""
solid-name: PromptContentResolver
solid-category: service
solid-spec: [SPEC-027]
solid-description: Resolves references to prompt content in step configurations.
"""

from __future__ import annotations

import os
from pathlib import Path

from harness.models import FlowValidationError
from harness.prompt_content_resolving import PromptContentResolving
from utils.prompt_builder import TextFileReading


class PromptContentResolver(PromptContentResolving):

    def __init__(self, reader: TextFileReading) -> None:
        self._reader = reader

    def resolve(self, step: dict, flow_file_path: str) -> dict:
        prompt_file = step.get("prompt_file")
        if prompt_file is None:
            return step

        flow_dir = Path(os.path.abspath(flow_file_path)).parent
        content = self._reader.read(flow_dir / prompt_file)
        if content is None:
            raise FlowValidationError(
                f"Step '{step.get('id')}' prompt_file not found: '{prompt_file}'"
            )

        resolved = dict(step)
        resolved["prompt"] = content
        del resolved["prompt_file"]
        return resolved
