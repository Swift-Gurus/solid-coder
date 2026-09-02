"""Records outputs from completed step instances."""

from __future__ import annotations

from harness.event_appender import EventAppending
from harness.models import StepInstance
from harness.output_recording import OutputRecording


"""
solid-name: OutputRecorder
solid-category: service
solid-spec: [SPEC-031, SPEC-037]
solid-description: Records completed step outputs with explicit execution and owning-workflow identities.
"""
class OutputRecorder(OutputRecording):

    def __init__(self, event_appender: EventAppending) -> None:
        self._event_appender = event_appender

    def record(self, events_path: str, ready: list[StepInstance], step_outputs: dict, session_id: str) -> None:
        addressed = [
            instance
            for instance in ready
            if instance.instance_id in step_outputs
        ]
        for instance in addressed:
            workflow_instance = instance.workflow_instance
            local_step_id = (
                workflow_instance.steps.require_execution(
                    instance.step_id
                ).local_step_id
                if workflow_instance is not None
                else None
            )
            pending_siblings = [
                sibling
                for sibling in ready
                if sibling.step_id == instance.step_id
            ]
            addressed_siblings = [
                sibling
                for sibling in pending_siblings
                if sibling.instance_id in step_outputs
            ]
            completes_parent = (
                len(addressed_siblings) == len(pending_siblings)
                and instance == addressed_siblings[-1]
            )
            self._event_appender.append(events_path, "step_completed", {
                "instance_id": instance.instance_id,
                "step_id": instance.step_id,
                "outputs": step_outputs[instance.instance_id],
                "session_id": session_id,
                "iteration_index": instance.iteration_index,
                "workflow_source_index": (
                    workflow_instance.source_index
                    if workflow_instance is not None
                    else None
                ),
                "workflow_instance_id": (
                    workflow_instance.instance_id
                    if workflow_instance is not None
                    else None
                ),
                "parent_workflow_instance_id": (
                    workflow_instance.owner_instance_id
                    if workflow_instance is not None
                    else None
                ),
                "local_step_id": local_step_id,
                "item": instance.item,
                "parent_completed": completes_parent,
                "empty_collection": instance.automatic_outputs is not None,
            })
            self._event_appender.append(events_path, "session_step_recorded", {
                "session_id": session_id,
                "instance_id": instance.instance_id,
            })
