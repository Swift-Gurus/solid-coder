"""
solid-name: test_swiftui_validation_flow
solid-category: integration-test
solid-spec: [SPEC-039]
solid-description: Verifies SwiftUI applicability, canonical instructions, independently scored observations, exceptions, and audited results.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_PROJECT_ROOT / "mcp-server"))

from rule_metric_expectation import RuleMetricExpectation  # noqa: E402
from rule_validation_flow_contract import RuleValidationFlowContract  # noqa: E402
from rule_validation_scenario import RuleValidationScenario  # noqa: E402


class TestSwiftUIValidationFlow(RuleValidationFlowContract):
    __test__ = True
    PROJECT_ROOT = _PROJECT_ROOT
    SCENARIO = RuleValidationScenario(
        workflow_id="swiftui",
        rule_path=(
            _PROJECT_ROOT
            / "references"
            / "coding"
            / "apple"
            / "SwiftUI"
            / "rule.md"
        ),
        fixture_path=(
            _PROJECT_ROOT
            / "tests"
            / "coding"
            / "apple"
            / "swiftui"
            / "fixtures"
            / "fixture-1.swift"
        ),
        metrics=[
            RuleMetricExpectation(step_id="body_nesting_depth", metric_id="SUI-1", observation_id="body_nesting_depth", detection_id="SUI-1", detection_name="Body Complexity", value=3, severity="SEVERE"),
            RuleMetricExpectation(step_id="view_expression_count", metric_id="SUI-1", observation_id="view_expression_count", detection_id="SUI-1", detection_name="Body Complexity", value=8, severity="SEVERE"),
            RuleMetricExpectation(step_id="impure_count", metric_id="SUI-2", detection_id="SUI-2", detection_name="View Purity", value=1, severity="SEVERE"),
            RuleMetricExpectation(step_id="max_modifier_chain", metric_id="SUI-3", detection_id="SUI-3", detection_name="Modifier Chain Length", value=2, severity="SEVERE"),
            RuleMetricExpectation(step_id="vm_injection_style", metric_id="SUI-4", detection_id="SUI-4", detection_name="ViewModel Injection", value="concrete", severity="SEVERE"),
            RuleMetricExpectation(step_id="preview_only_count", metric_id="SUI-5", detection_id="SUI-5", detection_name="Preview-Only View Containment", value=1, severity="SEVERE"),
            RuleMetricExpectation(step_id="views_without_preview_count", metric_id="SUI-6", detection_id="SUI-6", detection_name="Preview Coverage", value=2, severity="SEVERE"),
            RuleMetricExpectation(step_id="bad_accessibility_count", metric_id="SUI-7", detection_id="SUI-7", detection_name="Accessibility Identifier on Containers", value=1, severity="SEVERE"),
            RuleMetricExpectation(step_id="fixed_frame_count", metric_id="SUI-8", detection_id="SUI-8", detection_name="Adaptive Sizing", value=1, severity="SEVERE"),
            RuleMetricExpectation(step_id="over_isolated_count", metric_id="SUI-9", detection_id="SUI-9", detection_name="Actor Isolation Granularity", value=1, severity="SEVERE"),
        ],
        final_severity="SEVERE",
        included_file_extensions=[".swift"],
        included_unit_kinds=["struct"],
        included_tags=["swiftui", "view"],
    )
