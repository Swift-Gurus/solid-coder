"""Defines completion eligibility for one materialized rule execution."""

from typing import Protocol

from harness.rule_execution_instance import RuleExecutionInstance
from harness.run_state import RunState


"""
solid-name: RuleExecutionCompletionEvaluating
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for deciding whether a rule execution has completed observations that require deterministic finalization.
"""
class RuleExecutionCompletionEvaluating(Protocol):
    def evaluate(
        self,
        instance: RuleExecutionInstance,
        run_state: RunState,
    ) -> bool: ...
