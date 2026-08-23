"""
solid-name: test_structured_concurrency_validation_flow
solid-category: integration-test
solid-spec: [SPEC-039]
solid-description: Verifies structured-concurrency applicability, canonical instructions, typed observations, scoring, exceptions, and audit behavior.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_PROJECT_ROOT / "mcp-server"))

from rule_metric_expectation import RuleMetricExpectation  # noqa: E402
from rule_validation_flow_contract import RuleValidationFlowContract  # noqa: E402
from rule_validation_scenario import RuleValidationScenario  # noqa: E402


class TestStructuredConcurrencyValidationFlow(RuleValidationFlowContract):
    __test__ = True
    PROJECT_ROOT = _PROJECT_ROOT
    SCENARIO = RuleValidationScenario(
        workflow_id="structured-concurrency",
        rule_path=(
            _PROJECT_ROOT
            / "references"
            / "coding"
            / "apple"
            / "StructuredConcurrency"
            / "rule.md"
        ),
        fixture_path=(
            _PROJECT_ROOT
            / "tests"
            / "coding"
            / "apple"
            / "structured-concurrency"
            / "fixtures"
            / "fixture-1.swift"
        ),
        metrics=[
            RuleMetricExpectation(step_id="model_mixing", metric_id="SC-1", detection_id="SC-1", detection_name="Concurrency Model Mixing", value=1, severity="SEVERE"),
            RuleMetricExpectation(step_id="orphaned_tasks", metric_id="SC-2", detection_id="SC-2", detection_name="Unstructured Task Lifecycle", value=1, severity="SEVERE"),
            RuleMetricExpectation(step_id="safety_bypasses", metric_id="SC-3", detection_id="SC-3", detection_name="Concurrency Safety Bypasses", value=1, severity="SEVERE"),
            RuleMetricExpectation(step_id="independent_sequential_awaits", metric_id="SC-4", detection_id="SC-4", detection_name="Sequential vs Concurrent Await", value=3, severity="SEVERE"),
            RuleMetricExpectation(step_id="blocking_bridges", metric_id="SC-5", detection_id="SC-5", detection_name="Sync-to-Async Bridging", value=1, severity="SEVERE"),
            RuleMetricExpectation(step_id="raw_duration_count", metric_id="SC-6", detection_id="SC-6", detection_name="Duration API", value=1, severity="SEVERE"),
        ],
        final_severity="SEVERE",
        included_file_extensions=[".swift"],
        included_tags=["structured-concurrency"],
    )
