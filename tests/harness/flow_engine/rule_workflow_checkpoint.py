"""Defines accumulated state for prerequisite rule-analysis tests."""

from __future__ import annotations

from dataclasses import dataclass

from harness.flow_next_result import FlowNextResult
from harness.flow_start_result import FlowStartResult


"""
solid-name: RuleWorkflowCheckpoint
solid-category: test-support
solid-spec: [SPEC-039]
solid-description: Carries the current flow result and prompts observed through prerequisite analysis.
"""
@dataclass(frozen=True)
class RuleWorkflowCheckpoint:
    run_id: str
    result: FlowStartResult | FlowNextResult
    prompts: list[str]
