"""Defines deterministic finalization of one executable rule instance."""

from pathlib import Path
from typing import Protocol

from harness.rule_execution_instance import RuleExecutionInstance
from harness.rule_review_result import RuleReviewResult
from harness.run_state import RunState


"""
solid-name: RuleExecutionFinalizing
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for scoring, persisting, and auditing one completed executable rule instance.
"""
class RuleExecutionFinalizing(Protocol):
    def finalize(
        self,
        run_directory: Path,
        events_path: str,
        instance: RuleExecutionInstance,
        run_state: RunState,
    ) -> RuleReviewResult: ...
