"""Records durable workflow-step skip decisions."""

from __future__ import annotations

from harness.condition_serializing import ConditionSerializing
from harness.event_appender import EventAppending
from harness.step_instance import StepInstance
from harness.step_skip_recording import StepSkipRecording


"""
solid-name: StepSkipRecorder
solid-category: service
solid-spec: [SPEC-037]
solid-description: Records conditionally skipped workflow-step instances as durable events.
"""
class StepSkipRecorder(StepSkipRecording):
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
        ready: list[StepInstance],
    ) -> None:
        skipped_instances = [instance for instance in ready if instance.skip is not None]
        for instance in skipped_instances:
            skip = instance.skip
            if skip is None:
                continue
            workflow_instance = instance.workflow_instance
            local_step_id = (
                workflow_instance.steps.require_execution(
                    instance.step_id
                ).local_step_id
                if workflow_instance is not None
                else None
            )
            siblings = [
                sibling
                for sibling in ready
                if sibling.step_id == instance.step_id
            ]
            skipped_siblings = [
                sibling for sibling in siblings if sibling.skip is not None
            ]
            parent_completed = (
                len(skipped_siblings) == len(siblings)
                and instance == skipped_siblings[-1]
            )
            self._event_appender.append(
                events_path,
                "step_skipped",
                {
                    "step_id": skip.step_id,
                    "instance_id": skip.instance_id,
                    "condition": self._condition_serializer.serialize(skip.condition),
                    "evidence": skip.evidence.model_dump(mode="json"),
                    "item": skip.item,
                    "iteration_index": skip.iteration_index,
                    "workflow_instance_id": (
                        workflow_instance.instance_id
                        if workflow_instance is not None
                        else None
                    ),
                    "local_step_id": local_step_id,
                    "workflow_source_index": (
                        workflow_instance.source_index
                        if workflow_instance is not None
                        else None
                    ),
                    "parent_completed": parent_completed,
                },
            )
