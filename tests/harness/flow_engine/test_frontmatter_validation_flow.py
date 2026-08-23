"""
solid-name: test_frontmatter_validation_flow
solid-category: integration-test
solid-spec: [SPEC-039]
solid-description: Verifies file-scoped frontmatter instructions, scalar scoring, metric exclusions, and audited results.
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


class TestFrontmatterValidationFlow(RuleValidationFlowContract):
    __test__ = True
    PROJECT_ROOT = _PROJECT_ROOT
    SCENARIO = RuleValidationScenario(
        workflow_id="frontmatter",
        rule_path=(
            _PROJECT_ROOT
            / "references"
            / "principles"
            / "frontmatter"
            / "rule.md"
        ),
        fixture_path=(
            _PROJECT_ROOT
            / "tests"
            / "principles"
            / "frontmatter"
            / "fixtures"
            / "fixture-1.swift"
        ),
        metrics=[
            RuleMetricExpectation(step_id="missing_frontmatter_count", metric_id="FM-1", detection_id="FM-1", detection_name="Missing Frontmatter", value=1, severity="SEVERE"),
            RuleMetricExpectation(step_id="name_mismatch_count", metric_id="FM-2", detection_id="FM-2", detection_name="Name Mismatch", value=0, severity="COMPLIANT"),
            RuleMetricExpectation(step_id="invalid_category_count", metric_id="FM-3", detection_id="FM-3", detection_name="Invalid Category", value=0, severity="COMPLIANT"),
            RuleMetricExpectation(step_id="incorrect_stack_count", metric_id="FM-4", detection_id="FM-4", detection_name="Incorrect Stack", value=0, severity="COMPLIANT"),
            RuleMetricExpectation(step_id="bad_description_count", metric_id="FM-5", detection_id="FM-5", detection_name="Bad Description", value=0, severity="COMPLIANT"),
        ],
        final_severity="SEVERE",
        rule_scope=RuleScope.FILE,
        has_authored_exceptions=False,
    )
