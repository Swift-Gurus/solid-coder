"""Parses the supported collection metric source-reference grammar."""

from harness.collection_source_reference import CollectionSourceReference
from harness.collection_source_reference_parsing import (
    CollectionSourceReferenceParsing,
)
from harness.step_output_reference_parsing import StepOutputReferenceParsing
from harness.step_output_reference_syntax_error import (
    StepOutputReferenceSyntaxError,
)
from harness.workflow_output_reference import WorkflowOutputReference

"""
solid-name: CollectionSourceReferenceParser
solid-category: boundary
solid-spec: [SPEC-053, SPEC-056]
solid-description: Parses collection sources from local step outputs or projected child-workflow outputs.
"""


class CollectionSourceReferenceParser(CollectionSourceReferenceParsing):
    def __init__(
        self,
        step_reference_parser: StepOutputReferenceParsing,
    ) -> None:
        self._step_reference_parser = step_reference_parser

    def parse(self, expression: str) -> CollectionSourceReference:
        components = expression.split(".")
        if components[0] == "steps":
            return self._step_reference_parser.parse(expression)
        if (
            len(components) == 4
            and components[0] == "workflows"
            and components[1]
            and components[2] == "outputs"
            and components[3]
        ):
            return WorkflowOutputReference(
                workflow_alias=components[1],
                output_name=components[3],
            )
        raise StepOutputReferenceSyntaxError(expression)
