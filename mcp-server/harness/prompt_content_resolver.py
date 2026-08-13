"""Applies external prompt content to workflow steps."""

from __future__ import annotations

from harness.prompt_file_loading import PromptFileLoading
from harness.prompt_file_path_resolving import PromptFilePathResolving
from harness.prompt_content_resolving import PromptContentResolving
from harness.resolved_prompt_applying import ResolvedPromptApplying
from harness.step_declaration import StepDeclaration


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
        prompt_applier: ResolvedPromptApplying,
    ) -> None:
        self._path_resolver = path_resolver
        self._prompt_loader = prompt_loader
        self._prompt_applier = prompt_applier

    def resolve(
        self,
        step: StepDeclaration,
        flow_file_path: str,
    ) -> StepDeclaration:
        prompt_file = step.prompt_file
        if not isinstance(prompt_file, str):
            return step

        prompt_path = self._path_resolver.resolve(step, flow_file_path, prompt_file)
        step_id = step.id if isinstance(step.id, str) else ""
        content = self._prompt_loader.load(prompt_path, step_id, prompt_file)
        return self._prompt_applier.apply(step, content)
