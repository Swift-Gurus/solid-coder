"""
solid-name: AttemptFailure
solid-category: model
solid-spec: [SPEC-027, SPEC-037]
solid-description: Carries one attributed workflow-step attempt failure for durable recording.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AttemptFailure:
    step_id: str
    reason: str
    reopen: bool
    attempt_id: str | None = None
