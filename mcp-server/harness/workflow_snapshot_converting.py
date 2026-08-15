"""Defines conversion of typed workflows into snapshot values."""

from __future__ import annotations

from typing import Protocol

from harness.flow_def import FlowDef


"""
solid-name: WorkflowSnapshotConverting
solid-category: abstraction
solid-spec: [SPEC-031]
solid-description: Contract for converting typed workflows into durable snapshot values.
"""
class WorkflowSnapshotConverting(Protocol):
    def convert(self, flow_def: FlowDef) -> dict[str, object]: ...
