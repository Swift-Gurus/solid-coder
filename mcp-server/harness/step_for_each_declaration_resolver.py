"""Selects one step's effective iteration declaration."""

from typing import Optional

from harness.for_each_declaration import ForEachDeclaration
from harness.models import StepDef
from harness.step_for_each_declaration_resolving import (
    StepForEachDeclarationResolving,
)


"""
solid-name: StepForEachDeclarationResolver
solid-category: service
solid-spec: [SPEC-042]
solid-description: Selects iteration controls declared directly by a step or inherited from its included-workflow instance.
"""
class StepForEachDeclarationResolver(StepForEachDeclarationResolving):
    def resolve(self, step: StepDef) -> Optional[ForEachDeclaration]:
        if step.for_each is not None:
            return step.for_each
        if step.workflow_instance is not None:
            return step.workflow_instance.for_each
        return None
