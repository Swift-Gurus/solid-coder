"""Defines immutable workflow-step dependency replacement."""

from typing import Protocol

from harness.step_declaration import StepDeclaration


"""
solid-name: StepDependenciesReplacing
solid-category: abstraction
solid-spec: [SPEC-058]
solid-description: Contract for replacing typed workflow-step dependencies while preserving the remaining declaration.
"""
class StepDependenciesReplacing(Protocol):
    def replace_dependencies(
        self,
        step: StepDeclaration,
        dependencies: list[str],
    ) -> StepDeclaration: ...
