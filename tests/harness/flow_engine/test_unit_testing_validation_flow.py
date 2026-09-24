"""
solid-name: test_unit_testing_validation_flow
solid-category: integration-test
solid-spec: [SPEC-039, SPEC-055]
solid-description: Verifies unit-test applicability, canonical instructions, typed observations, scoring, exceptions, and audit behavior.
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
        analysis=[
            RuleAnalysisExpectation(
                step_id="classify_test_observations",
                output={
                    "observations": [
                        {
                            "classification": classification,
                            "location": location,
                            "is_exception": False,
                            "reasoning": reasoning,
                            "evidence": evidence,
                        }
                        for classification, location, reasoning, evidence in (
                            (
                                "ISOLATION_VIOLATION",
                                "CheckoutTests.sharedResult",
                                "The test suite owns shared mutable static state.",
                                "static var sharedResult = false",
                            ),
                            (
                                "STRUCTURE_VIOLATION",
                                "CheckoutTests.test1",
                                "The test body contains conditional assertion logic.",
                                "if service.canCheckout { XCTAssertTrue(...) }",
                            ),
                            (
                                "STRUCTURE_VIOLATION",
                                "CheckoutTests.testSave",
                                "The assertion compares a value to itself.",
                                "XCTAssertEqual(service.total, service.total)",
                            ),
                            (
                                "NAMING_VIOLATION",
                                "CheckoutTests.test1",
                                "The name is generic and states no outcome.",
                                "func test1()",
                            ),
                            (
                                "NAMING_VIOLATION",
                                "CheckoutTests.testSave",
                                "The name gives only a method-like action.",
                                "func testSave()",
                            ),
                            (
                                "NAMING_VIOLATION",
                                "CheckoutTests.testBasic",
                                "The name is generic and states no scenario.",
                                "func testBasic()",
                            ),
                            (
                                "TEST_DOUBLE_VIOLATION",
                                "CheckoutTests.testBasic",
                                "The test sets and reads the same mock value.",
                                "mock.formatted = \"$10\" followed by asserting mock.formatted",
                            ),
                            (
                                "SETUP_VIOLATION",
                                "CheckoutTests",
                                "The SUT is constructed inline in multiple tests.",
                                "CheckoutService() appears in test1 and testSave.",
                            ),
                            (
                                "FRAMEWORK_VIOLATION",
                                "fixture-1.swift",
                                "A non-UI unit test file uses XCTest.",
                                "import XCTest and CheckoutTests: XCTestCase",
                            ),
                        )
                    ],
                },
            ),
        ],
        metrics=[
            RuleMetricExpectation(step_id="isolation_violations", metric_id="TEST-1", detection_id="TEST-1", detection_name="Test Isolation", value=1, severity="SEVERE", mcp_owned=True),
            RuleMetricExpectation(step_id="structure_violations", metric_id="TEST-2", detection_id="TEST-2", detection_name="Test Structure", value=2, severity="SEVERE", mcp_owned=True),
            RuleMetricExpectation(step_id="naming_violations", metric_id="TEST-3", detection_id="TEST-3", detection_name="Test Naming", value=3, severity="SEVERE", mcp_owned=True),
            RuleMetricExpectation(step_id="test_double_violations", metric_id="TEST-4", detection_id="TEST-4", detection_name="Test Double Quality", value=1, severity="SEVERE", mcp_owned=True),
            RuleMetricExpectation(step_id="setup_violations", metric_id="TEST-5", detection_id="TEST-5", detection_name="Test Setup Complexity", value=1, severity="SEVERE", mcp_owned=True),
            RuleMetricExpectation(step_id="framework_violations", metric_id="TEST-6", detection_id="TEST-6", detection_name="Testing Framework", value=1, severity="SEVERE", mcp_owned=True),
        ],
        final_severity="SEVERE",
        rule_scope=RuleScope.FILE,
        included_file_extensions=[".swift"],
        included_tags=["unit-test"],
    )

    def test_observation_exception_excludes_only_matching_metric(self) -> None:
        started = self._start()
        observations = [
            {
                **observation,
                "is_exception": observation["location"] == "CheckoutTests.sharedResult",
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
                    "reasoning": "Only the shared-state observation is exempt.",
                    "evidence": "All remaining test violations still apply.",
                },
            },
        })

        self.assertEqual(completed.status, "done", completed.error)
        result = self._rule_result(started.run_id)
        metrics = {metric.metric_id: metric for metric in result.metrics}
        self.assertEqual(metrics["TEST-1"].value, 0)
        self.assertEqual(metrics["TEST-1"].severity, "COMPLIANT")
        self.assertEqual(metrics["TEST-2"].value, 2)
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
            ["classify_test_observations"],
        )
        self.assertIn("evidence", rejected.steps[0].rejection_reason)
