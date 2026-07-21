"""
solid-name: OutputRecorder
solid-category: service
solid-spec: [SPEC-013]
solid-description: Records outputs from completed step instances.
"""

from __future__ import annotations

from harness.event_appender import EventAppending
from harness.models import StepInstance
from harness.output_recording import OutputRecording


class OutputRecorder(OutputRecording):

    def __init__(self, event_appender: EventAppending) -> None:
        self._event_appender = event_appender

    def record(self, events_path: str, ready: list[StepInstance], step_outputs: dict, session_id: str) -> None:
        for instance in ready:
            instance_outputs = step_outputs.get(instance.instance_id, {})
            self._event_appender.append(events_path, "step_completed", {
                "instance_id": instance.instance_id,
                "step_id": instance.step_id,
                "outputs": instance_outputs,
                "session_id": session_id,
            })
            self._event_appender.append(events_path, "session_step_recorded", {
                "session_id": session_id,
                "instance_id": instance.instance_id,
            })