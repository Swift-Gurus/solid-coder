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
            len(components) < 4
            or components[0] != "steps"
            or any(not component for component in components[1:-2])
            or any(
                self._is_runtime_identity_component(component)
                for component in components[1:-2]
            )
            or components[-2] != "outputs"
            or not components[-1]
        ):
            raise StepOutputReferenceSyntaxError(expression)
        return StepOutputReference(
            step_id=".".join(components[1:-2]),
            output_name=components[-1],
        )

    def _is_runtime_identity_component(self, component: str) -> bool:
        prefix, separator, source_index = component.rpartition("-")
        return bool(prefix and separator and source_index.isdigit())
