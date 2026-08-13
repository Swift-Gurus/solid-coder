"""Defines resolution of every output belonging to one workflow step."""

from pathlib import Path
from typing import Protocol

from harness.output_spec import OutputSpec
from harness.step_declaration import StepDeclaration


"""
solid-name: OutputCollectionResolving
solid-category: abstraction
solid-spec: [SPEC-027, SPEC-035]
solid-description: Contract for resolving the complete output declaration collection of one workflow step.
"""
class OutputCollectionResolving(Protocol):

    def resolve(
        self,
        step: StepDeclaration,
        declaring_file: Path,
    ) -> list[OutputSpec]:
        ...
