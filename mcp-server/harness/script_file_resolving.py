"""Defines script-file resolution for workflow steps."""

from typing import Protocol

from harness.step_declaration import StepDeclaration


"""
solid-name: ScriptFileResolving
solid-category: abstraction
solid-spec: [SPEC-035]
solid-description: Contract for resolving a workflow step's declared script file into executable step data.
"""
class ScriptFileResolving(Protocol):
    def resolve(
        self,
        step: StepDeclaration,
        flow_file_path: str,
    ) -> StepDeclaration: ...
