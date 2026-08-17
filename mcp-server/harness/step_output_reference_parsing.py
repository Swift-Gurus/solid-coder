"""Defines parsing of authored workflow step-output expressions."""

from typing import Protocol

from harness.step_output_reference import StepOutputReference


"""
solid-name: StepOutputReferenceParsing
solid-category: abstraction
solid-spec: [SPEC-030, SPEC-037]
solid-description: Contract for converting one authored step-output expression into a typed local reference.
"""
class StepOutputReferenceParsing(Protocol):
    def parse(self, expression: str) -> StepOutputReference: ...
