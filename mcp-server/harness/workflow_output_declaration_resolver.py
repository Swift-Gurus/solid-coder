"""Resolves one authored reusable-workflow output."""

from __future__ import annotations

from pathlib import Path

from harness.authored_workflow_output import AuthoredWorkflowOutput
from harness.flow_validation_error import FlowValidationError
from harness.output_schema_file_loading import OutputSchemaFileLoading
from harness.output_spec import OutputSpec
from harness.step_output_reference_parsing import StepOutputReferenceParsing
from harness.step_output_reference_syntax_error import StepOutputReferenceSyntaxError
from harness.workflow_expression_parsing import WorkflowExpressionParsing
from harness.workflow_output_declaration import WorkflowOutputDeclaration
from harness.workflow_output_declaration_resolving import (
    WorkflowOutputDeclarationResolving,
)


"""
solid-name: WorkflowOutputDeclarationResolver
solid-category: boundary
solid-spec: [SPEC-037]
solid-description: Transforms one authored workflow output into its executable declaration.
"""
class WorkflowOutputDeclarationResolver(WorkflowOutputDeclarationResolving):

    def __init__(
        self,
        expression_parser: WorkflowExpressionParsing,
        reference_parser: StepOutputReferenceParsing,
        schema_loader: OutputSchemaFileLoading,
    ) -> None:
        self._expression_parser = expression_parser
        self._reference_parser = reference_parser
        self._schema_loader = schema_loader

    def resolve(
        self,
        output: AuthoredWorkflowOutput,
        declaring_file: str,
    ) -> WorkflowOutputDeclaration:
        schema = (
            self._schema_loader.load(
                Path(declaring_file),
                output.schema_file,
                "<workflow>",
                output.name,
            )
            if output.schema_file is not None
            else output.schema_value
        )
        expression = self._expression_parser.parse(output.value)
        try:
            reference = self._reference_parser.parse(expression.value)
        except StepOutputReferenceSyntaxError as error:
            raise FlowValidationError(
                f"Workflow output '{output.name}' must reference an internal step output"
            ) from error
        return WorkflowOutputDeclaration(
            specification=OutputSpec(
                name=output.name,
                type=output.type,
                schema=schema,
            ),
            reference=reference,
        )
