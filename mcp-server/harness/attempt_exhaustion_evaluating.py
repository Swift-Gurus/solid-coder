"""Defines evaluation of workflow attempt budgets."""

from __future__ import annotations

from typing import Protocol

from harness.exhausted_attempt import ExhaustedAttempt
from harness.models import FlowDef, RunState


"""
solid-name: AttemptExhaustionEvaluating
solid-category: abstraction
solid-spec: [SPEC-010, SPEC-031]
solid-description: Contract for identifying an exhausted workflow execution attempt.
"""
class AttemptExhaustionEvaluating(Protocol):
    def evaluate(
        self,
        flow_def: FlowDef,
        run_state: RunState,
    ) -> ExhaustedAttempt | None: ...
