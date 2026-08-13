from __future__ import annotations

from typing import Protocol

from harness.step_declaration import StepDeclaration


"""
solid-name: PromptContentResolving
solid-category: abstraction
solid-spec: [SPEC-027]
solid-description: Contract for resolving prompt content for a workflow-step declaration.
"""
class PromptContentResolving(Protocol):

    def resolve(
        self,
        step: StepDeclaration,
        flow_file_path: str,
    ) -> StepDeclaration: ...
