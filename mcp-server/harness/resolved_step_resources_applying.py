"""Defines application of resolved resources to a workflow step."""

from typing import Protocol

from harness.resolved_step_resources import ResolvedStepResources
from harness.step_declaration import StepDeclaration


"""
solid-name: ResolvedStepResourcesApplying
solid-category: abstraction
solid-spec: [SPEC-027, SPEC-035]
solid-description: Contract for applying resolved resources to a workflow-step declaration.
"""
class ResolvedStepResourcesApplying(Protocol):

    def apply(
        self,
        step: StepDeclaration,
        resources: ResolvedStepResources,
    ) -> StepDeclaration: ...
