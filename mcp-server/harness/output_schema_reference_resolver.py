"""Resolves one file-backed output schema declaration."""

from pathlib import Path

from harness.output_spec import OutputSpec
from harness.output_schema_declaration_validating import OutputSchemaDeclarationValidating
from harness.output_schema_file_loading import OutputSchemaFileLoading
from harness.resolved_output_schema_applying import ResolvedOutputSchemaApplying
from harness.step_declaration import StepDeclaration
from harness.step_identity_resolving import StepIdentityResolving


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
        schema_applier: ResolvedOutputSchemaApplying,
        identity_resolver: StepIdentityResolving,
    ) -> None:
        self._declaration_validator = declaration_validator
        self._schema_loader = schema_loader
        self._schema_applier = schema_applier
        self._identity_resolver = identity_resolver

    def resolve(
        self,
        step: StepDeclaration,
        output: OutputSpec,
        declaring_file: Path,
    ) -> OutputSpec:
        schema_file = output.schema_file
        if schema_file is None:
            return output

        self._declaration_validator.validate(step, output)
        schema = self._schema_loader.load(
            declaring_file,
            schema_file,
            self._identity_resolver.resolve(step),
            output.name,
        )
        return self._schema_applier.apply(output, schema)
