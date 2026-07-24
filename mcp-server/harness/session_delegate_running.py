"""
solid-name: SessionDelegateRunning
solid-category: abstraction
solid-spec: [SPEC-027]
solid-description: Contract for executing a prompt and returning its step execution outcome.
"""

from __future__ import annotations

from typing import Protocol

from harness.step_run_outcome import StepRunOutcome


class SessionDelegateRunning(Protocol):

    def run(self, prompt: str) -> StepRunOutcome: ...
