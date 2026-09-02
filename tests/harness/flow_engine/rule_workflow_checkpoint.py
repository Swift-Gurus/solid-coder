"""Defines accumulated state for prerequisite rule-analysis tests."""

from __future__ import annotations

from dataclasses import dataclass

from harness.flow_next_result import FlowNextResult
from harness.flow_start_result import FlowStartResult


"""
solid-name: RuleWorkflowCheckpoint
solid-category: test-support
solid-spec: [SPEC-039]
solid-description: Carries a rule flow result and the model-facing steps observed while advancing it.
"""
@dataclass(frozen=True)
class RuleWorkflowCheckpoint:
    run_id: str
    result: FlowStartResult | FlowNextResult
    prompts: list[str]
    step_ids: list[str]
