"""Defines serialization of workflow result envelopes."""

from __future__ import annotations

from typing import Protocol

from harness.workflow_result_envelope import WorkflowResultEnvelope


"""
solid-name: WorkflowResultEnvelopeSerializing
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for serializing a workflow result envelope at an external rendering boundary.
"""
class WorkflowResultEnvelopeSerializing(Protocol):
    def serialize(
        self,
        envelope: WorkflowResultEnvelope,
    ) -> dict[str, object]: ...
