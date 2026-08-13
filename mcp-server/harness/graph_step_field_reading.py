"""Defines the fields required to validate a workflow-step graph."""

from __future__ import annotations

from typing import Protocol


"""
solid-name: GraphStepFieldReading
solid-category: abstraction
solid-spec: [SPEC-027]
solid-description: Contract for reading workflow-step identity and dependency fields.
"""
class GraphStepFieldReading(Protocol):
    id: object | None
    depends_on: object | None
