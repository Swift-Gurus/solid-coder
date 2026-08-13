"""Defines creation of workflow-step resource snapshots."""

from typing import Protocol

from harness.resolved_step_resources import ResolvedStepResources
from harness.step_declaration import StepDeclaration


"""
solid-name: ResolvedStepResourcesCreating
solid-category: abstraction
solid-spec: [SPEC-027, SPEC-035]
solid-description: Contract for creating a resource snapshot from a workflow-step declaration.
"""
class ResolvedStepResourcesCreating(Protocol):

    def create(self, step: StepDeclaration) -> ResolvedStepResources: ...
