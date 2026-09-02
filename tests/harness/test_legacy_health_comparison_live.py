"""Runs the locked legacy health smoke scenario through Codex Terra."""

from pathlib import Path

from legacy_health_comparison_e2e_live_base import (
    LegacyHealthComparisonE2ELiveBase,
)
from live_rule_validation_expectation import LiveRuleValidationExpectation
from rule_metric_result_expectation import RuleMetricResultExpectation


_PROJECT_ROOT = Path(__file__).resolve().parents[2]


"""
solid-name: TestCodexLegacyHealthComparisonLive
solid-category: integration-test
solid-spec: [SPEC-036, SPEC-041]
solid-description: Proves the legacy health comparison path completes under the pinned Codex Terra profile before repeated measurement.
"""
class TestCodexLegacyHealthComparisonLive(
    LegacyHealthComparisonE2ELiveBase,
):
    __test__ = True


"""
solid-name: TestCodexLegacySRPComparisonLive
solid-category: integration-test
solid-spec: [SPEC-036, SPEC-041]
solid-description: Runs the real legacy health checker with only SRP instructions and asserts the locked SRP fixture measurements.
"""
class TestCodexLegacySRPComparisonLive(
    LegacyHealthComparisonE2ELiveBase,
):
    __test__ = True
    ARTIFACT_SCENARIO = "legacy-srp-smoke"
    FIXTURE = (
        _PROJECT_ROOT
        / "tests"
        / "principles"
        / "SRP"
        / "fixtures"
        / "fixture-1.swift"
    )
    EXPECTED_RULE_IDS = ["srp"]
    EXPECTED_PROMPT_MARKERS = ["## SRP"]
    EXPECTED_UNIT_NAME = "ProductCatalog"
    EXPECTED_RULE = LiveRuleValidationExpectation(
        workflow_id="srp",
        metrics=[
            RuleMetricResultExpectation(
                step_id="verb_count",
                metric_id="SRP-1",
                value=6,
                severity="SEVERE",
            ),
            RuleMetricResultExpectation(
                step_id="cohesion_groups",
                metric_id="SRP-2",
                value=2,
                severity="SEVERE",
            ),
            RuleMetricResultExpectation(
                step_id="stakeholder_count",
                metric_id="SRP-3",
                value=2,
                severity="SEVERE",
            ),
        ],
        final_severity="SEVERE",
    )
