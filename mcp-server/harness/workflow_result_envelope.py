"""Defines one published result from an included workflow instance."""

from __future__ import annotations

from dataclasses import dataclass

from harness.workflow_output_values import WorkflowOutputValues


"""
solid-name: WorkflowResultEnvelope
solid-category: model
solid-spec: [SPEC-037]
solid-description: Carries stable instance identity, its source item, and validated declared workflow outputs.
"""
@dataclass(frozen=True)
class WorkflowResultEnvelope:
    instance_id: str
    item: object
    outputs: WorkflowOutputValues
