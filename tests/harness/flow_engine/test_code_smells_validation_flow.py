"""
solid-name: test_code_smells_validation_flow
solid-category: integration-test
solid-spec: [SPEC-039]
solid-description: Verifies file-scoped applicability, canonical smell instructions, typed observations, scoring, and audit behavior.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_PROJECT_ROOT / "mcp-server"))

from harness.rule_scope import RuleScope  # noqa: E402
from rule_metric_expectation import RuleMetricExpectation  # noqa: E402
from rule_validation_flow_contract import RuleValidationFlowContract  # noqa: E402
from rule_validation_scenario import RuleValidationScenario  # noqa: E402


class TestCodeSmellsValidationFlow(RuleValidationFlowContract):
    __test__ = True
    PROJECT_ROOT = _PROJECT_ROOT
    SCENARIO = RuleValidationScenario(
        workflow_id="code-smells",
        rule_path=(
            _PROJECT_ROOT
            / "references"
            / "principles"
            / "code-smells"
            / "rule.md"
        ),
        fixture_path=(
            _PROJECT_ROOT
            / "tests"
            / "principles"
            / "code-smells"
            / "fixtures"
            / "fixture-1.swift"
        ),
        metrics=[
            RuleMetricExpectation(
                step_id="static_logic_count",
                metric_id="CS-1",
                detection_id="CS-1",
                detection_name="Static Logic",
                value=1,
                severity="SEVERE",
            ),
            RuleMetricExpectation(
                step_id="class_struct_count",
                metric_id="CS-2",
                detection_id="CS-2",
                detection_name="Multiple Types Per File",
                value=2,
                severity="SEVERE",
            ),
            RuleMetricExpectation(
                step_id="inline_type_count",
                metric_id="CS-3",
                detection_id="CS-3",
                detection_name="Inline Type Definition",
                value=1,
                severity="SEVERE",
            ),
        ],
        final_severity="SEVERE",
        rule_scope=RuleScope.FILE,
        has_authored_exceptions=False,
    )
