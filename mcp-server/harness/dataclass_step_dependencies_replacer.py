"""Adapts dataclass replacement to workflow-step dependencies."""

from dataclasses import replace

from harness.step_declaration import StepDeclaration
from harness.step_dependencies_replacing import StepDependenciesReplacing

"""
solid-name: DataclassStepDependenciesReplacer
solid-category: adapter
solid-spec: [SPEC-058]
solid-description: Replaces typed workflow-step dependencies while preserving all other declaration fields.
"""


class DataclassStepDependenciesReplacer(StepDependenciesReplacing):
    def replace_dependencies(
        self,
        step: StepDeclaration,
        dependencies: list[str],
    ) -> StepDeclaration:
        return replace(step, depends_on=dependencies)
