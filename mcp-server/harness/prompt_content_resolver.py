"""Applies external prompt content to workflow steps."""

from __future__ import annotations

from harness.prompt_file_loading import PromptFileLoading
from harness.prompt_file_path_resolving import PromptFilePathResolving
from harness.prompt_content_resolving import PromptContentResolving


"""
solid-name: PromptContentResolver
solid-category: service
solid-spec: [SPEC-027, SPEC-035]
solid-description: Coordinates prompt path resolution and loading before applying text to one workflow step.
"""
class PromptContentResolver(PromptContentResolving):

    def __init__(
        self,
        path_resolver: PromptFilePathResolving,
        prompt_loader: PromptFileLoading,
    ) -> None:
        self._path_resolver = path_resolver
        self._prompt_loader = prompt_loader

    def resolve(self, step: dict, flow_file_path: str) -> dict:
        prompt_file = step.get("prompt_file")
        if prompt_file is None:
            return step

        prompt_path = self._path_resolver.resolve(step, flow_file_path, prompt_file)
        content = self._prompt_loader.load(prompt_path, step.get("id", ""), prompt_file)

        resolved = dict(step)
        resolved["prompt"] = content
        del resolved["prompt_file"]
        return resolved
