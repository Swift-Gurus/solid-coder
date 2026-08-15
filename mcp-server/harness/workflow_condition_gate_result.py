"""Defines the outcome of advancing a workflow-level condition gate."""

from __future__ import annotations

from dataclasses import dataclass


"""
solid-name: WorkflowConditionGateResult
solid-category: model
solid-spec: [SPEC-037]
solid-description: Represents workflow-condition progress and whether step execution is allowed.
"""
@dataclass(frozen=True)
class WorkflowConditionGateResult:
    progressed: bool
    allows_execution: bool
