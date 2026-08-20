"""
solid-name: test_ocp_validation_flow
solid-category: integration-test
solid-spec: [SPEC-039]
solid-description: Verifies canonical OCP instructions, typed observations, exception handling, scoring, and audit behavior.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_PROJECT_ROOT / "mcp-server"))

from rule_metric_expectation import RuleMetricExpectation  # noqa: E402
from rule_validation_flow_contract import RuleValidationFlowContract  # noqa: E402
from rule_validation_scenario import RuleValidationScenario  # noqa: E402


class TestOCPValidationFlow(RuleValidationFlowContract):
    __test__ = True
    PROJECT_ROOT = _PROJECT_ROOT
    SCENARIO = RuleValidationScenario(
        workflow_id="ocp",
        rule_path=_PROJECT_ROOT / "references" / "principles" / "OCP" / "rule.md",
        fixture_path=(
            _PROJECT_ROOT
            / "tests"
            / "principles"
            / "OCP"
            / "fixtures"
            / "fixture-1.swift"
        ),
        metrics=[
            RuleMetricExpectation(
                step_id="sealed_variation_points",
                metric_id="OCP-1",
                detection_id="OCP-1",
                detection_name="Sealed Variation Points",
                value=2,
                severity="SEVERE",
            ),
            RuleMetricExpectation(
                step_id="untestable_dependencies",
                metric_id="OCP-2",
                detection_id="OCP-2",
                detection_name="Testability",
                value=0,
                severity="COMPLIANT",
            ),
            RuleMetricExpectation(
                step_id="testable_direct_count",
                metric_id="OCP-3",
                detection_id="OCP-2",
                detection_name="Testability",
                value=0,
                severity="COMPLIANT",
            ),
        ],
        final_severity="SEVERE",
    )
