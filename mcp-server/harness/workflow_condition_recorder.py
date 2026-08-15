"""Records durable workflow-level condition decisions."""

from __future__ import annotations

from harness.condition_serializing import ConditionSerializing
from harness.event_appender import EventAppending
from harness.workflow_condition_decision import WorkflowConditionDecision
from harness.workflow_condition_recording import WorkflowConditionRecording


"""
solid-name: WorkflowConditionRecorder
solid-category: service
solid-spec: [SPEC-037]
solid-description: Records evaluated workflow eligibility as durable events.
"""
class WorkflowConditionRecorder(WorkflowConditionRecording):

    def __init__(
        self,
        event_appender: EventAppending,
        condition_serializer: ConditionSerializing,
    ) -> None:
        self._event_appender = event_appender
        self._condition_serializer = condition_serializer

    def record(
        self,
        events_path: str,
        decision: WorkflowConditionDecision,
    ) -> None:
        self._event_appender.append(
            events_path,
            "workflow_condition_evaluated",
            {
                "condition": self._condition_serializer.serialize(
                    decision.condition
                ),
                "matched": decision.matched,
            },
        )
