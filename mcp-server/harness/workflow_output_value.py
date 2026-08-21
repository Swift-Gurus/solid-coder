"""Defines one resolved workflow output value."""

from __future__ import annotations

from dataclasses import dataclass


"""
solid-name: WorkflowOutputValue
solid-category: model
solid-spec: [SPEC-037]
solid-description: Associates one declared workflow-output name with its validated runtime value.
"""
@dataclass(frozen=True)
class WorkflowOutputValue:
    name: str
    value: object
