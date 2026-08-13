"""
solid-description: Contract for converting input data into step specifications.
solid-category: abstraction
"""

from __future__ import annotations

from typing import Protocol

from harness.step_declaration import StepDeclaration
from harness.step_def import StepDef


"""
solid-name: StepBuilding
solid-category: abstraction
solid-spec: [SPEC-027, SPEC-030, SPEC-035]
solid-description: Contract for converting input data into executable step specifications.
"""
class StepBuilding(Protocol):
    def build(self, declaration: StepDeclaration) -> StepDef: ...
