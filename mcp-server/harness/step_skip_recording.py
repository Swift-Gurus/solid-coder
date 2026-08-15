"""Defines durable recording of skipped workflow-step instances."""

from __future__ import annotations

from typing import Protocol

from harness.step_instance import StepInstance


"""
solid-name: StepSkipRecording
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for recording conditionally skipped workflow-step instances.
"""
class StepSkipRecording(Protocol):
    def record(
        self,
        events_path: str,
        ready: list[StepInstance],
    ) -> None: ...
