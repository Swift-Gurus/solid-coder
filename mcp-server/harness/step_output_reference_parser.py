"""Parses authored workflow step-output expressions."""

from harness.step_output_reference import StepOutputReference
from harness.step_output_reference_parsing import StepOutputReferenceParsing
from harness.step_output_reference_syntax_error import (
    StepOutputReferenceSyntaxError,
)


"""
solid-name: StepOutputReferenceParser
solid-category: boundary
solid-spec: [SPEC-030, SPEC-037]
solid-description: Converts the supported authored step-output expression grammar into validated typed references.
"""
class StepOutputReferenceParser(StepOutputReferenceParsing):
    def parse(self, expression: str) -> StepOutputReference:
        components = expression.split(".")
        if (
            len(components) != 4
            or components[0] != "steps"
            or not components[1]
            or components[2] != "outputs"
            or not components[3]
        ):
            raise StepOutputReferenceSyntaxError(expression)
        return StepOutputReference(
            step_id=components[1],
            output_name=components[3],
        )
