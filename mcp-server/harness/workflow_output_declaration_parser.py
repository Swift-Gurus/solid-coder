"""Coordinates parsing of reusable-workflow output declarations."""

from __future__ import annotations

from harness.authored_workflow_outputs import AuthoredWorkflowOutputs
from harness.structured_model_decoding import StructuredModelDecoding
from harness.workflow_output_declaration import WorkflowOutputDeclaration
from harness.workflow_output_declaration_resolving import (
    WorkflowOutputDeclarationResolving,
)


"""
solid-name: WorkflowOutputDeclarationParser
solid-category: service
solid-spec: [SPEC-037]
solid-description: Coordinates typed decoding and executable resolution of authored workflow outputs.
"""
class WorkflowOutputDeclarationParser:

    def __init__(
        self,
        decoder: StructuredModelDecoding[AuthoredWorkflowOutputs],
        declaration_resolver: WorkflowOutputDeclarationResolving,
    ) -> None:
        self._decoder = decoder
        self._declaration_resolver = declaration_resolver

    def parse(
        self,
        raw_outputs: object,
        declaring_file: str,
    ) -> list[WorkflowOutputDeclaration]:
        if raw_outputs is None:
            return []
        decoded = self._decoder.decode(
            raw_outputs,
            "workflow outputs",
        )
        return [
            self._declaration_resolver.resolve(output, declaring_file)
            for output in decoded.root
        ]
