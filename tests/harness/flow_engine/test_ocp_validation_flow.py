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

from rule_analysis_expectation import RuleAnalysisExpectation  # noqa: E402
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
        analysis=[
            RuleAnalysisExpectation(
                step_id="analyze_dependencies",
                output={
                    "analysis": {
                        "dependencies": [
                            {
                                "name": "UserDefaults.standard",
                                "classification": "DIRECT_NON_INJECTED",
                                "is_exception": False,
                                "can_instantiate": True,
                                "can_subclass": False,
                                "reasoning": "Static access seals the dependency.",
                                "evidence": "OCP_SHARED_ANALYSIS_EVIDENCE",
                            }
                        ],
                        "has_hardcoded_behavior_selection": False,
                    }
                },
            ),
            RuleAnalysisExpectation(
                step_id="analyze_testability",
                output={
                    "testability": [
                        {
                            "name": "UserDefaults.standard",
                            "classification": "UNTESTABLE",
                            "reasoning": "The static access cannot be substituted.",
                            "evidence": "OCP_SHARED_TESTABILITY_EVIDENCE",
                        }
                    ]
                },
            ),
        ],
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

    def test_dependency_analysis_is_shared_by_every_ocp_metric(self) -> None:
        started = self._start()

        self.assertEqual(
            [step.step_id for step in started.steps],
            ["analyze_dependencies"],
        )
        dependency_analysis = self.sut.flow_next({
            started.steps[0].instance_id: {
                "analysis": {
                    "dependencies": [
                        {
                            "name": "UserDefaults.standard",
                            "classification": "DIRECT_NON_INJECTED",
                            "is_exception": False,
                            "can_instantiate": True,
                            "can_subclass": False,
                            "reasoning": "Static access seals the dependency.",
                            "evidence": "OCP_SHARED_ANALYSIS_EVIDENCE",
                        }
                    ],
                    "has_hardcoded_behavior_selection": False,
                }
            }
        })

        self.assertEqual(
            {step.step_id for step in dependency_analysis.steps},
            {
                "sealed_variation_points",
                "analyze_testability",
                "classify_exception",
            },
        )
        self.assertTrue(
            all(
                "OCP_SHARED_ANALYSIS_EVIDENCE" in step.prompt
                for step in dependency_analysis.steps
            )
        )
        exception_step = next(
            step for step in dependency_analysis.steps
            if step.step_id == "classify_exception"
        )
        self.assertIn(
            "dependency array is literally empty",
            exception_step.prompt,
        )
        self.assertIn(
            "does not make the reviewed unit itself a pure data structure",
            exception_step.prompt,
        )
        self.assertIn(
            "MUST return `is_exception: true`",
            exception_step.prompt,
        )
        testability_step = next(
            step for step in dependency_analysis.steps
            if step.step_id == "analyze_testability"
        )
        measured = self.sut.flow_next({
            testability_step.instance_id: {
                "testability": [
                    {
                        "name": "UserDefaults.standard",
                        "classification": "UNTESTABLE",
                        "reasoning": "The static access cannot be substituted.",
                        "evidence": "OCP_SHARED_TESTABILITY_EVIDENCE",
                    }
                ]
            }
        })

        downstream = {
            step.step_id: step.prompt
            for step in measured.steps
        }
        self.assertIn("untestable_dependencies", downstream)
        self.assertIn("testable_direct_count", downstream)
        self.assertIn(
            "OCP_SHARED_TESTABILITY_EVIDENCE",
            downstream["untestable_dependencies"],
        )
        self.assertIn(
            "OCP_SHARED_TESTABILITY_EVIDENCE",
            downstream["testable_direct_count"],
        )
        self.assertIn(
            "not exceptions",
            downstream["testable_direct_count"],
        )
