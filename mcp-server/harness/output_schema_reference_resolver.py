"""Resolves one file-backed output schema declaration."""

from pathlib import Path

from harness.output_schema_declaration_validating import OutputSchemaDeclarationValidating
from harness.output_schema_file_loading import OutputSchemaFileLoading


"""
solid-name: OutputSchemaReferenceResolver
solid-category: service
solid-spec: [SPEC-027, SPEC-035]
solid-description: Validates and loads a single file-backed output schema from its declaring workflow.
"""
class OutputSchemaReferenceResolver:

    def __init__(
        self,
        declaration_validator: OutputSchemaDeclarationValidating,
        schema_loader: OutputSchemaFileLoading,
    ) -> None:
        self._declaration_validator = declaration_validator
        self._schema_loader = schema_loader

    def resolve(self, step: dict, output: dict, declaring_file: Path) -> dict:
        schema_file = output.get("schema_file")
        if schema_file is None:
            return output

        self._declaration_validator.validate(step, output)
        schema = self._schema_loader.load(
            declaring_file,
            schema_file,
            step.get("id", ""),
            output.get("name", ""),
        )
        resolved = dict(output)
        resolved["schema"] = schema
        del resolved["schema_file"]
        return resolved
