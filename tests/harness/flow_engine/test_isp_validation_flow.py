"""
solid-name: test_isp_validation_flow
solid-category: integration-test
solid-spec: [SPEC-039]
solid-description: Verifies canonical ISP instructions, protocol applicability, typed observations, exception handling, scoring, and audit behavior.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_PROJECT_ROOT / "mcp-server"))

from rule_metric_expectation import RuleMetricExpectation  # noqa: E402
from rule_validation_flow_contract import RuleValidationFlowContract  # noqa: E402
from rule_validation_scenario import RuleValidationScenario  # noqa: E402


class TestISPValidationFlow(RuleValidationFlowContract):
    __test__ = True
    PROJECT_ROOT = _PROJECT_ROOT
    SCENARIO = RuleValidationScenario(
        workflow_id="isp",
        rule_path=_PROJECT_ROOT / "references" / "principles" / "ISP" / "rule.md",
        fixture_path=(
            _PROJECT_ROOT
            / "tests"
            / "principles"
            / "ISP"
            / "fixtures"
            / "fixture-1.swift"
        ),
        metrics=[
            RuleMetricExpectation(
                step_id="width",
                metric_id="ISP-1",
                detection_id="ISP-1",
                detection_name="Protocol Width",
                value=10,
                severity="SEVERE",
            ),
            RuleMetricExpectation(
                step_id="min_coverage",
                metric_id="ISP-2",
                detection_id="ISP-2",
                detection_name="Conformer Coverage",
                value=50,
                severity="SEVERE",
            ),
            RuleMetricExpectation(
                step_id="cohesion_groups",
                metric_id="ISP-3",
                detection_id="ISP-3",
                detection_name="Protocol Cohesion Groups",
                value=2,
                severity="SEVERE",
            ),
        ],
        final_severity="SEVERE",
        included_unit_kinds=["protocol"],
    )
