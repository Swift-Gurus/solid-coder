"""
solid-name: RunStartedEventLogging
solid-category: abstraction
solid-spec: [SPEC-031]
solid-description: Contract for recording a run's start event.
"""

from __future__ import annotations

from typing import Protocol


class RunStartedEventLogging(Protocol):
    def record(self, events_path: str, run_id: str, flow_name: str) -> None: ...