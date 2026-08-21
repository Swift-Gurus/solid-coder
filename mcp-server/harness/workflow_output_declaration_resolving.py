"""Defines resolution of one authored workflow output."""

from __future__ import annotations

from typing import Protocol

from harness.authored_workflow_output import AuthoredWorkflowOutput
from harness.workflow_output_declaration import WorkflowOutputDeclaration


"""
solid-name: WorkflowOutputDeclarationResolving
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for resolving one typed authored output into its executable workflow declaration.
"""
class WorkflowOutputDeclarationResolving(Protocol):
    def resolve(
        self,
        output: AuthoredWorkflowOutput,
        declaring_file: str,
    ) -> WorkflowOutputDeclaration: ...
