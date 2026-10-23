"""Determines whether a rule execution has completed observations."""

from harness.rule_execution_completion_evaluating import (
    RuleExecutionCompletionEvaluating,
)
from harness.rule_execution_instance import RuleExecutionInstance
from harness.run_state import RunState

"""
solid-name: RuleExecutionCompletionEvaluator
solid-category: service
solid-spec: [SPEC-039]
solid-description: Identifies rule executions with completed metric or exception observations that require finalization.
"""


class RuleExecutionCompletionEvaluator(RuleExecutionCompletionEvaluating):
    def evaluate(
        self,
        instance: RuleExecutionInstance,
        run_state: RunState,
    ) -> bool:
        return any(
            step.id in run_state.completed
            or (
                instance.workflow.declaration.exception is not None
                and any(
                    candidate.id in run_state.completed for candidate in instance.steps
                )
                and step.id in run_state.skipped
                and step.metric is not None
                and step.metric.unavailable_reason is not None
            )
            for step in instance.steps
            if step.type in {"metric", "exception"} or step.assessment is not None
        )
