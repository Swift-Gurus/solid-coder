"""Defines durable recording of workflow-level condition decisions."""

from __future__ import annotations

from typing import Protocol

from harness.workflow_condition_decision import WorkflowConditionDecision


"""
solid-name: WorkflowConditionRecording
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for durably recording workflow-level condition decisions.
"""
class WorkflowConditionRecording(Protocol):
    def record(
        self,
        events_path: str,
        decision: WorkflowConditionDecision,
    ) -> None: ...
