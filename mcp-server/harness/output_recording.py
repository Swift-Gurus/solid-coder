"""
solid-name: OutputRecording
solid-category: abstraction
solid-spec: [SPEC-031]
solid-description: Contract for recording step completion, outputs, and session-to-step mappings.
"""

from __future__ import annotations

from typing import Protocol

from harness.models import StepInstance


class OutputRecording(Protocol):

    def record(self, events_path: str, ready: list[StepInstance], step_outputs: dict, session_id: str) -> None: ...