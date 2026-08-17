"""Applies persisted workflow-level condition decisions to run state."""

from __future__ import annotations

from harness.condition_parsing import ConditionParsing
from harness.unavailable_condition_evidence import UnavailableConditionEvidence
from harness.workflow_condition_decision import WorkflowConditionDecision
from harness.workflow_condition_evaluated_event import (
    WorkflowConditionEvaluatedEvent,
)


"""
solid-name: WorkflowConditionEvaluatedTransition
solid-category: service
solid-spec: [SPEC-037]
solid-description: Restores durable workflow eligibility decisions during event replay.
"""
class WorkflowConditionEvaluatedTransition:

    def __init__(self, condition_parser: ConditionParsing) -> None:
        self._condition_parser = condition_parser

    def apply(self, state: dict, event: dict) -> None:
        evaluated_event = WorkflowConditionEvaluatedEvent.model_validate(event)
        evidence = evaluated_event.evidence or UnavailableConditionEvidence(
            matched=evaluated_event.matched
        )
        state["workflow_condition_decision"] = WorkflowConditionDecision(
            condition=self._condition_parser.parse(evaluated_event.condition),
            evidence=evidence,
        )
