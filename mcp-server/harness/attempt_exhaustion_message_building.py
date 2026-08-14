"""Defines construction of exhausted-attempt diagnostics."""

from __future__ import annotations

from typing import Protocol

from harness.exhausted_attempt import ExhaustedAttempt
from harness.models import RunState


"""
solid-name: AttemptExhaustionMessageBuilding
solid-category: abstraction
solid-spec: [SPEC-010, SPEC-031]
solid-description: Contract for constructing an exhausted workflow-attempt diagnostic.
"""
class AttemptExhaustionMessageBuilding(Protocol):
    def build(
        self,
        exhausted: ExhaustedAttempt,
        run_state: RunState,
        events_path: str,
    ) -> str: ...
