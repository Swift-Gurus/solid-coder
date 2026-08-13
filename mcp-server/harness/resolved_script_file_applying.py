"""Defines application of a resolved script path to a workflow step."""

from typing import Protocol

from harness.step_declaration import StepDeclaration


"""
solid-name: ResolvedScriptFileApplying
solid-category: abstraction
solid-spec: [SPEC-035]
solid-description: Contract for applying a resolved script path to a workflow-step declaration.
"""
class ResolvedScriptFileApplying(Protocol):

    def apply(
        self,
        step: StepDeclaration,
        script_file: str,
    ) -> StepDeclaration: ...
