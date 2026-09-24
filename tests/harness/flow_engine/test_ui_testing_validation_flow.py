"""
solid-name: test_ui_testing_validation_flow
solid-category: integration-test
solid-spec: [SPEC-039, SPEC-055]
solid-description: Verifies UI-test applicability, canonical instructions, typed observations, scoring, exceptions, and audit behavior.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_PROJECT_ROOT / "mcp-server"))

from rule_analysis_expectation import RuleAnalysisExpectation  # noqa: E402
from rule_metric_expectation import RuleMetricExpectation  # noqa: E402
from rule_validation_flow_contract import RuleValidationFlowContract  # noqa: E402
from rule_validation_scenario import RuleValidationScenario  # noqa: E402
from harness.rule_scope import RuleScope  # noqa: E402


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
        analysis=[
            RuleAnalysisExpectation(
                step_id="classify_ui_test_observations",
                output={
                    "observations": [
                        *(
                            {
                                "classification": "FLOW_VIOLATION",
                                "location": method,
                                "is_exception": False,
                                "reasoning": "The test inlines a three-step navigation flow.",
                                "evidence": "Shop, Cart, and Checkout taps occur directly in the test.",
                            }
                            for method in (
                                "CheckoutUITests.testCheckoutTitle",
                                "CheckoutUITests.testCheckoutButton",
                            )
                        ),
                        {
                            "classification": "BASE_CLASS_VIOLATION",
                            "location": "CheckoutUITests",
                            "is_exception": False,
                            "reasoning": "The suite directly owns app launch lifecycle.",
                            "evidence": "CheckoutUITests inherits XCTestCase and launches app in setUp().",
                        },
                        {
                            "classification": "GROUPING_VIOLATION",
                            "location": "CheckoutUITests checkout-state methods",
                            "is_exception": False,
                            "reasoning": "Two tests repeat the same flow to assert one property each.",
                            "evidence": "testCheckoutTitle and testCheckoutButton repeat Shop/Cart/Checkout.",
                        },
                        *(
                            {
                                "classification": "SYNC_VIOLATION",
                                "location": f"synchronization-site-{index}",
                                "is_exception": False,
                                "reasoning": "The interaction or assertion has no condition wait.",
                                "evidence": evidence,
                            }
                            for index, evidence in enumerate(
                                (
                                    "testCheckoutTitle Shop tap",
                                    "testCheckoutTitle Cart tap",
                                    "testCheckoutTitle Checkout tap",
                                    "testCheckoutTitle Thread.sleep",
                                    "testCheckoutTitle Checkout exists assertion",
                                    "testCheckoutButton Shop tap",
                                    "testCheckoutButton Cart tap",
                                    "testCheckoutButton Checkout tap",
                                    "testCheckoutButton Pay exists assertion",
                                ),
                                start=1,
                            )
                        ),
                        *(
                            {
                                "classification": "IDENTIFIER_VIOLATION",
                                "location": f"identifier-site-{index}",
                                "is_exception": False,
                                "reasoning": "The element query uses a raw string identifier.",
                                "evidence": evidence,
                            }
                            for index, evidence in enumerate(
                                (
                                    'buttons["Shop"] in testCheckoutTitle',
                                    'buttons["Cart"] in testCheckoutTitle',
                                    'buttons["Checkout"] in testCheckoutTitle',
                                    'staticTexts["Checkout"] in testCheckoutTitle',
                                    'buttons["Shop"] in testCheckoutButton',
                                    'buttons["Cart"] in testCheckoutButton',
                                    'buttons["Checkout"] in testCheckoutButton',
                                    'buttons["Pay"] in testCheckoutButton',
                                ),
                                start=1,
                            )
                        ),
                    ],
                },
            ),
        ],
        metrics=[
            RuleMetricExpectation(step_id="flow_violations", metric_id="UITEST-1", detection_id="UITEST-1", detection_name="Flow Encapsulation", value=2, severity="SEVERE", mcp_owned=True),
            RuleMetricExpectation(step_id="base_class_violations", metric_id="UITEST-2", detection_id="UITEST-2", detection_name="Base Class Structure", value=1, severity="SEVERE", mcp_owned=True),
            RuleMetricExpectation(step_id="grouping_violations", metric_id="UITEST-3", detection_id="UITEST-3", detection_name="Assertion Grouping", value=1, severity="SEVERE", mcp_owned=True),
            RuleMetricExpectation(step_id="sync_violations", metric_id="UITEST-4", detection_id="UITEST-4", detection_name="Synchronization", value=9, severity="SEVERE", mcp_owned=True),
            RuleMetricExpectation(step_id="identifier_violations", metric_id="UITEST-5", detection_id="UITEST-5", detection_name="Typed Identifiers", value=8, severity="SEVERE", mcp_owned=True),
        ],
        final_severity="SEVERE",
        rule_scope=RuleScope.FILE,
        included_file_extensions=[".swift"],
        included_tags=["ui-test"],
    )

    def test_observation_exception_excludes_only_matching_metric(self) -> None:
        started = self._start()
        observations = [
            {
                **observation,
                "is_exception": observation["location"] == "CheckoutUITests",
            }
            for observation in self.SCENARIO.analysis[0].output["observations"]
        ]

        exception = self.sut.flow_next({
            started.steps[0].instance_id: {"observations": observations},
        })
        completed = self.sut.flow_next({
            exception.steps[0].instance_id: {
                "is_exception": False,
                "additional_info": {
                    "reasoning": "Only the lifecycle observation is exempt.",
                    "evidence": "All flow, grouping, synchronization, and identifier findings remain.",
                },
            },
        })

        self.assertEqual(completed.status, "done", completed.error)
        result = self._rule_result(started.run_id)
        metrics = {metric.metric_id: metric for metric in result.metrics}
        self.assertEqual(metrics["UITEST-2"].value, 0)
        self.assertEqual(metrics["UITEST-2"].severity, "COMPLIANT")
        self.assertEqual(metrics["UITEST-4"].value, 9)
        self.assertEqual(result.severity, "SEVERE")

    def test_rejects_an_observation_without_required_evidence(self) -> None:
        started = self._start()
        invalid = dict(self.SCENARIO.analysis[0].output["observations"][0])
        invalid.pop("evidence")

        rejected = self.sut.flow_next({
            started.steps[0].instance_id: {"observations": [invalid]},
        })

        self.assertEqual(rejected.status, "ready")
        self.assertEqual(
            [step.step_id for step in rejected.steps],
            ["classify_ui_test_observations"],
        )
        self.assertIn("evidence", rejected.steps[0].rejection_reason)
