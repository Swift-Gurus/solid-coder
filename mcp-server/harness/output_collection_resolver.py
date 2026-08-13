"""Resolves every output belonging to one workflow step."""

from pathlib import Path

from harness.output_spec import OutputSpec
from harness.output_schema_reference_resolving import OutputSchemaReferenceResolving
from harness.step_declaration import StepDeclaration


"""
solid-name: OutputCollectionResolver
solid-category: service
solid-spec: [SPEC-027, SPEC-035]
solid-description: Applies schema-reference resolution across one step's declared output collection.
"""
class OutputCollectionResolver:

    def __init__(self, schema_reference_resolver: OutputSchemaReferenceResolving) -> None:
        self._schema_reference_resolver = schema_reference_resolver

    def resolve(
        self,
        step: StepDeclaration,
        declaring_file: Path,
    ) -> list[OutputSpec]:
        return [
            self._schema_reference_resolver.resolve(step, output, declaring_file)
            for output in step.outputs
        ]
