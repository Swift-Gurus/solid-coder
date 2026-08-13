from __future__ import annotations

from typing import Protocol

from harness.step_declaration import StepDeclaration


"""
solid-name: OutputSchemaResolving
solid-category: abstraction
solid-spec: [SPEC-027]
solid-description: Contract for resolving schema references within a workflow-step declaration.
"""
class OutputSchemaResolving(Protocol):

    def resolve(
        self,
        step: StepDeclaration,
        flow_file_path: str,
    ) -> StepDeclaration: ...
