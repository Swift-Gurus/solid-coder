"""Defines the backend-neutral live Structured Concurrency expectations."""

from __future__ import annotations

from pathlib import Path

from rule_validation_e2e_live_base import RuleValidationE2ELiveBase


_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_FIXTURE = (
    _PROJECT_ROOT
    / "tests"
    / "coding"
    / "apple"
    / "structured-concurrency"
    / "fixtures"
    / "fixture-1.swift"
)


"""
solid-name: StructuredConcurrencyValidationE2ELiveBase
solid-category: test-support
solid-spec: [SPEC-039, SPEC-055]
solid-description: Supplies the Structured Concurrency scenario and locked MCP-scored observations to the shared live rule contract.
"""
class StructuredConcurrencyValidationE2ELiveBase(RuleValidationE2ELiveBase):
    WORKFLOW_ID = "structured-concurrency"
    ARTIFACT_SCENARIO = "structured-concurrency"
    FIXTURE = _FIXTURE
    EXPECTED_STEP_IDS = [
        "model_mixing",
        "orphaned_tasks",
        "safety_bypasses",
        "independent_sequential_awaits",
        "blocking_bridges",
        "raw_duration_count",
    ]
    EXPECTED_METRIC_IDS = [
        "SC-1",
        "SC-2",
        "SC-3",
        "SC-4",
        "SC-5",
        "SC-6",
    ]
    EXPECTED_VALUES = [1, 1, 1, 3, 1, 1]
    EXPECTED_METRIC_SEVERITIES = ["SEVERE"] * 6
    EXPECTED_FINAL_SEVERITY = "SEVERE"
    ALLOW_AUXILIARY_STEPS = True
