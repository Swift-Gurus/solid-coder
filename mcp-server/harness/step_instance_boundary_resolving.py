"""Declares ready-step workflow-boundary resolution."""

from __future__ import annotations

from typing import Protocol

from harness.flow_def import FlowDef
from harness.step_instance import StepInstance


"""
solid-name: StepInstanceBoundaryResolving
solid-category: abstraction
solid-spec: [SPEC-045]
solid-description: Contract for identifying the workflow boundary that owns a ready step instance.
"""
class StepInstanceBoundaryResolving(Protocol):
    def resolve(self, flow: FlowDef, instance: StepInstance) -> str: ...
