"""Defines the resolved transformation policy for one nested child group."""

from __future__ import annotations

from dataclasses import dataclass

from harness.workflow_execution_mode import WorkflowExecutionMode


"""
solid-name: NestedIncludeChildGroupPolicy
solid-category: model
solid-spec: [SPEC-027, SPEC-035, SPEC-045]
solid-description: Carries resolved nested child-group ownership and presentation decisions.
"""
@dataclass(frozen=True)
class NestedIncludeChildGroupPolicy:
    owner_alias: str | None
    execution: WorkflowExecutionMode
    combines_presentation: bool
