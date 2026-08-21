"""Serializes typed workflow outputs for durable snapshots."""

from __future__ import annotations

from harness.workflow_output_declaration import WorkflowOutputDeclaration
from harness.workflow_output_snapshot_serializing import (
    WorkflowOutputSnapshotSerializing,
)


"""
solid-name: WorkflowOutputSnapshotSerializer
solid-category: boundary
solid-spec: [SPEC-037]
solid-description: Produces durable snapshots of declared workflow outputs.
"""
class WorkflowOutputSnapshotSerializer(WorkflowOutputSnapshotSerializing):
    def serialize(
        self,
        outputs: list[WorkflowOutputDeclaration],
    ) -> list[dict[str, object]]:
        serialized: list[dict[str, object]] = []
        for output in outputs:
            specification = output.specification
            reference = output.reference
            entry: dict[str, object] = {
                "name": specification.name,
                "type": specification.type,
                "value": (
                    f"steps.{reference.step_id}.outputs.{reference.output_name}"
                ),
            }
            if specification.schema is not None:
                entry["schema"] = specification.schema
            serialized.append(entry)
        return serialized
