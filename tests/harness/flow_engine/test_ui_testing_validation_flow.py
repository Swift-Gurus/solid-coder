"""
solid-name: test_ui_testing_validation_flow
solid-category: integration-test
solid-spec: [SPEC-039]
solid-description: Verifies UI-test applicability, canonical instructions, typed observations, scoring, exceptions, and audit behavior.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_PROJECT_ROOT / "mcp-server"))

from rule_metric_expectation import RuleMetricExpectation  # noqa: E402
from rule_validation_flow_contract import RuleValidationFlowContract  # noqa: E402
from rule_validation_scenario import RuleValidationScenario  # noqa: E402


class TestUITestingValidationFlow(RuleValidationFlowContract):
    __test__ = True
    PROJECT_ROOT = _PROJECT_ROOT
    SCENARIO = RuleValidationScenario(
        workflow_id="ui-testing",
        rule_path=(
            _PROJECT_ROOT
            / "references"
            / "validators"
            / "apple"
            / "ui-testing"
            / "rule.md"
        ),
        fixture_path=(
            _PROJECT_ROOT
            / "tests"
            / "validators"
            / "apple"
            / "ui-testing"
            / "fixtures"
            / "fixture-1.swift"
        ),
        metrics=[
            RuleMetricExpectation(step_id="flow_violations", metric_id="UITEST-1", detection_id="UITEST-1", detection_name="Flow Encapsulation", value=2, severity="SEVERE"),
            RuleMetricExpectation(step_id="base_class_violations", metric_id="UITEST-2", detection_id="UITEST-2", detection_name="Base Class Structure", value=1, severity="SEVERE"),
            RuleMetricExpectation(step_id="grouping_violations", metric_id="UITEST-3", detection_id="UITEST-3", detection_name="Assertion Grouping", value=1, severity="SEVERE"),
            RuleMetricExpectation(step_id="sync_violations", metric_id="UITEST-4", detection_id="UITEST-4", detection_name="Synchronization", value=9, severity="SEVERE"),
            RuleMetricExpectation(step_id="identifier_violations", metric_id="UITEST-5", detection_id="UITEST-5", detection_name="Typed Identifiers", value=8, severity="SEVERE"),
        ],
        final_severity="SEVERE",
        included_file_extensions=[".swift"],
        included_tags=["ui-test"],
    )
