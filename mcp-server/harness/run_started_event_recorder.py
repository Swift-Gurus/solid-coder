"""
solid-name: RunStartedEventRecorder
solid-category: service
solid-spec: [SPEC-013]
solid-description: Records a run start event.
"""

from __future__ import annotations

from harness.event_appender import EventAppending
from harness.run_started_event_logging import RunStartedEventLogging


class RunStartedEventRecorder(RunStartedEventLogging):

    def __init__(self, event_appender: EventAppending) -> None:
        self._event_appender = event_appender

    def record(self, events_path: str, run_id: str, flow_name: str) -> None:
        self._event_appender.append(events_path, "run_started", {"run_id": run_id, "flow": flow_name})
