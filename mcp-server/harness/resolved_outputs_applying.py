"""Defines application of resolved outputs to a workflow step."""

from typing import Protocol

from harness.output_spec import OutputSpec
from harness.step_declaration import StepDeclaration


"""
solid-name: ResolvedOutputsApplying
solid-category: abstraction
solid-spec: [SPEC-027, SPEC-035]
solid-description: Contract for applying resolved outputs to a workflow-step declaration.
"""
class ResolvedOutputsApplying(Protocol):

    def apply(
        self,
        step: StepDeclaration,
        outputs: list[OutputSpec],
    ) -> StepDeclaration: ...
