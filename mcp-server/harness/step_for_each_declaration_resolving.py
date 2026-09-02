"""Defines lookup of one step's effective iteration declaration."""

from typing import Optional, Protocol

from harness.for_each_declaration import ForEachDeclaration
from harness.models import StepDef


"""
solid-name: StepForEachDeclarationResolving
solid-category: abstraction
solid-spec: [SPEC-042]
solid-description: Contract for selecting the iteration declaration owned by an ordinary step or its included-workflow instance.
"""
class StepForEachDeclarationResolving(Protocol):
    def resolve(self, step: StepDef) -> Optional[ForEachDeclaration]: ...
