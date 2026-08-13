"""Adds output requirements to workflow-step prompts."""

from __future__ import annotations

from dataclasses import replace

from harness.step_declaration import StepDeclaration
from harness.step_prompt_augmenting import StepPromptAugmenting


"""
solid-name: StepPromptAugmenter
solid-category: service
solid-spec: [SPEC-027]
solid-description: Adds new output requirements to an existing workflow-step prompt.
"""
class StepPromptAugmenter(StepPromptAugmenting):
    def augment(
        self,
        step: StepDeclaration,
        requirements: list[str],
    ) -> StepDeclaration:
        prompt = step.prompt
        if not isinstance(prompt, str) or not prompt:
            return step
        additions = [requirement for requirement in requirements if requirement not in prompt]
        if not additions:
            return step
        return replace(step, prompt="\n\n".join([prompt, *additions]))
