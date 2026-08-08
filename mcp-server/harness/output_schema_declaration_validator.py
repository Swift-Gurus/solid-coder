"""Validates one output schema declaration."""

from harness.flow_validation_error_creating import FlowValidationErrorCreating


"""
solid-name: OutputSchemaDeclarationValidator
solid-category: service
solid-spec: [SPEC-027]
solid-description: Validates that an output declares at most one inline or file-backed schema source.
"""
class OutputSchemaDeclarationValidator:

    def __init__(self, error_factory: FlowValidationErrorCreating) -> None:
        self._error_factory = error_factory

    def validate(self, step: dict, output: dict) -> None:
        if output.get("schema") is not None and output.get("schema_file") is not None:
            raise self._error_factory.create(
                f"Step '{step.get('id')}' output '{output.get('name')}' must declare at most one "
                f"of 'schema' or 'schema_file'"
            )
