"""Serializes workflow result envelopes for external rendering."""

from __future__ import annotations

from harness.workflow_result_envelope import WorkflowResultEnvelope
from harness.workflow_result_envelope_serializing import (
    WorkflowResultEnvelopeSerializing,
)


"""
solid-name: WorkflowResultEnvelopeSerializer
solid-category: boundary
solid-spec: [SPEC-037]
solid-description: Serializes workflow result envelopes into externally renderable values.
"""
class WorkflowResultEnvelopeSerializer(WorkflowResultEnvelopeSerializing):
    def serialize(
        self,
        envelope: WorkflowResultEnvelope,
    ) -> dict[str, object]:
        return {
            "instance_id": envelope.instance_id,
            "item": envelope.item,
            "outputs": {
                output.name: output.value
                for output in envelope.outputs.entries
            },
        }
