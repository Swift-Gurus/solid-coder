"""
solid-name: test_unit_testing_validation_flow
solid-category: integration-test
solid-spec: [SPEC-039]
solid-description: Verifies unit-test applicability, canonical instructions, typed observations, scoring, exceptions, and audit behavior.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_PROJECT_ROOT / "mcp-server"))

from rule_metric_expectation import RuleMetricExpectation  # noqa: E402
from rule_validation_flow_contract import RuleValidationFlowContract  # noqa: E402
from rule_validation_scenario import RuleValidationScenario  # noqa: E402


class TestUnitTestingValidationFlow(RuleValidationFlowContract):
    __test__ = True
    PROJECT_ROOT = _PROJECT_ROOT
    SCENARIO = RuleValidationScenario(
        workflow_id="unit-testing",
        rule_path=(
            _PROJECT_ROOT / "references" / "testing" / "unit" / "swift" / "rule.md"
        ),
        fixture_path=(
            _PROJECT_ROOT
            / "tests"
            / "testing"
            / "unit"
            / "swift"
            / "fixtures"
            / "fixture-1.swift"
        ),
        metrics=[
            RuleMetricExpectation(step_id="isolation_violations", metric_id="TEST-1", detection_id="TEST-1", detection_name="Test Isolation", value=1, severity="SEVERE"),
            RuleMetricExpectation(step_id="structure_violations", metric_id="TEST-2", detection_id="TEST-2", detection_name="Test Structure", value=2, severity="SEVERE"),
            RuleMetricExpectation(step_id="naming_violations", metric_id="TEST-3", detection_id="TEST-3", detection_name="Test Naming", value=3, severity="SEVERE"),
            RuleMetricExpectation(step_id="test_double_violations", metric_id="TEST-4", detection_id="TEST-4", detection_name="Test Double Quality", value=1, severity="SEVERE"),
            RuleMetricExpectation(step_id="setup_violations", metric_id="TEST-5", detection_id="TEST-5", detection_name="Test Setup Complexity", value=1, severity="SEVERE"),
            RuleMetricExpectation(step_id="framework_violations", metric_id="TEST-6", detection_id="TEST-6", detection_name="Testing Framework", value=1, severity="SEVERE"),
        ],
        final_severity="SEVERE",
        included_file_extensions=[".swift"],
        included_tags=["unit-test"],
    )
