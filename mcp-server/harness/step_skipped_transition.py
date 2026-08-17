"""Applies a persisted step-skipped event to reconstructed run state."""

from __future__ import annotations

from harness.condition_parsing import ConditionParsing
from harness.step_skip import StepSkip
from harness.step_skipped_event import StepSkippedEvent


"""
solid-name: StepSkippedTransition
solid-category: service
solid-spec: [SPEC-037]
solid-description: Restores a durable workflow-step skip decision into run state.
"""
class StepSkippedTransition:
    def __init__(self, condition_parser: ConditionParsing) -> None:
        self._condition_parser = condition_parser

    def apply(self, state: dict, event: dict) -> None:
        skipped_event = StepSkippedEvent.model_validate(event)
        skip = StepSkip(
            step_id=skipped_event.step_id,
            instance_id=skipped_event.instance_id,
            condition=self._condition_parser.parse(skipped_event.condition),
            evidence=skipped_event.evidence,
            item=skipped_event.item,
            iteration_index=skipped_event.iteration_index,
            workflow_instance_id=skipped_event.workflow_instance_id,
            local_step_id=skipped_event.local_step_id,
            workflow_source_index=skipped_event.workflow_source_index,
        )
        skipped_instances = state.setdefault("skipped_instances", {})
        skipped_instances[skip.instance_id] = skip
        if skipped_event.parent_completed:
            skipped_steps = state.setdefault("skipped", {})
            skipped_steps[skip.step_id] = skip
        if skip.step_id in state["running"]:
            state["running"].remove(skip.step_id)
