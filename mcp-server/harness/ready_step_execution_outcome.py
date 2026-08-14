"""Defines the outcome of one ready-step execution attempt."""

from __future__ import annotations

from dataclasses import dataclass

from harness.flow_next_result import FlowNextResult


"""
solid-name: ReadyStepExecutionOutcome
solid-category: model
solid-spec: [SPEC-010, SPEC-027]
solid-description: Represents progress and terminal state from one ready workflow-step execution attempt.
"""
@dataclass(frozen=True)
class ReadyStepExecutionOutcome:
    progressed: bool
    terminal: FlowNextResult | None = None
