"""
solid-name: test_lsp_validation_flow
solid-category: integration-test
solid-spec: [SPEC-039]
solid-description: Verifies canonical LSP instructions, typed observations, exception handling, scoring, and audit behavior.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_PROJECT_ROOT / "mcp-server"))

from rule_metric_expectation import RuleMetricExpectation  # noqa: E402
from rule_validation_flow_contract import RuleValidationFlowContract  # noqa: E402
from rule_validation_scenario import RuleValidationScenario  # noqa: E402


class TestLSPValidationFlow(RuleValidationFlowContract):
    __test__ = True
    PROJECT_ROOT = _PROJECT_ROOT
    SCENARIO = RuleValidationScenario(
        workflow_id="lsp",
        rule_path=_PROJECT_ROOT / "references" / "principles" / "LSP" / "rule.md",
        fixture_path=(
            _PROJECT_ROOT
            / "tests"
            / "principles"
            / "LSP"
            / "fixtures"
            / "fixture-1.swift"
        ),
        metrics=[
            RuleMetricExpectation(
                step_id="type_checks",
                metric_id="LSP-1",
                detection_id="LSP-1",
                detection_name="Type Check Count",
                value=0,
                severity="COMPLIANT",
            ),
            RuleMetricExpectation(
                step_id="contract_violations",
                metric_id="LSP-2",
                detection_id="LSP-2",
                detection_name="Contract Compliance",
                value=0,
                severity="COMPLIANT",
            ),
            RuleMetricExpectation(
                step_id="fatal_error_methods",
                metric_id="LSP-3",
                detection_id="LSP-3",
                detection_name="Empty Methods",
                value=1,
                severity="SEVERE",
            ),
            RuleMetricExpectation(
                step_id="empty_methods",
                metric_id="LSP-4",
                detection_id="LSP-3",
                detection_name="Empty Methods",
                value=0,
                severity="COMPLIANT",
            ),
        ],
        final_severity="SEVERE",
    )
