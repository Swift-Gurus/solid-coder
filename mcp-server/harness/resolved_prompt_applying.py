"""Defines application of resolved prompt content to a workflow step."""

from typing import Protocol

from harness.step_declaration import StepDeclaration


"""
solid-name: ResolvedPromptApplying
solid-category: abstraction
solid-spec: [SPEC-027, SPEC-035]
solid-description: Contract for applying resolved prompt content to a workflow-step declaration.
"""
class ResolvedPromptApplying(Protocol):

    def apply(self, step: StepDeclaration, prompt: str) -> StepDeclaration: ...
