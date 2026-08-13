"""Defines validated workflow-step identity resolution."""

from __future__ import annotations

from typing import Protocol

from harness.graph_step_field_reading import GraphStepFieldReading


"""
solid-name: StepIdentityResolving
solid-category: abstraction
solid-spec: [SPEC-027]
solid-description: Contract for resolving a valid workflow-step identifier.
"""
class StepIdentityResolving(Protocol):
    def resolve(self, step: GraphStepFieldReading) -> str: ...
