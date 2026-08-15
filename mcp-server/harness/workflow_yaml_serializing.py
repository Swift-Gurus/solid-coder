"""Defines serialization of resolved workflows into durable YAML text."""

from __future__ import annotations

from typing import Protocol

from harness.flow_def import FlowDef


"""
solid-name: WorkflowYamlSerializing
solid-category: abstraction
solid-spec: [SPEC-031, SPEC-037]
solid-description: Contract for serializing resolved workflows into durable YAML text.
"""
class WorkflowYamlSerializing(Protocol):
    def serialize(self, flow_def: FlowDef) -> str: ...
