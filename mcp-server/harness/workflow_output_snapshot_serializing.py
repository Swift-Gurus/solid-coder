"""Defines durable serialization of workflow outputs."""

from __future__ import annotations

from typing import Protocol

from harness.workflow_output_declaration import WorkflowOutputDeclaration


"""
solid-name: WorkflowOutputSnapshotSerializing
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for serializing typed workflow outputs into their durable YAML representation.
"""
class WorkflowOutputSnapshotSerializing(Protocol):
    def serialize(
        self,
        outputs: list[WorkflowOutputDeclaration],
    ) -> list[dict[str, object]]: ...
