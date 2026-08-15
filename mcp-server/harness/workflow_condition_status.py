"""Defines model-facing workflow-level condition status."""

from __future__ import annotations

from dataclasses import dataclass


"""
solid-name: WorkflowConditionStatus
solid-category: model
solid-spec: [SPEC-037]
solid-description: Captures a workflow eligibility result and its declared condition summary.
"""
@dataclass(frozen=True)
class WorkflowConditionStatus:
    matched: bool
    condition: dict[str, object]
