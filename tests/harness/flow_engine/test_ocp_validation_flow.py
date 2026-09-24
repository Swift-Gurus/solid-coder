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
                    "dependencies": [
                        {
                            "name": "UserDefaults.standard",
                            "classification": "DIRECT_NON_INJECTED",
                            "has_business_logic": False,
                            "has_behavioral_dependencies": False,
                            "has_side_effecting_behavior": True,
                            "can_substitute_without_modifying_unit": False,
                            "can_subclass": False,
                            "can_instantiate": True,
                            "reasoning": "The unit directly accesses persistent preferences.",
                            "evidence": "OCP_USER_DEFAULTS_EVIDENCE",
                        },
                        {
                            "name": "NotificationCenter.default",
                            "classification": "DIRECT_NON_INJECTED",
                            "has_business_logic": False,
                            "has_behavioral_dependencies": False,
                            "has_side_effecting_behavior": True,
                            "can_substitute_without_modifying_unit": False,
                            "can_subclass": False,
                            "can_instantiate": True,
                            "reasoning": "The unit directly posts runtime notifications.",
                            "evidence": "OCP_NOTIFICATION_CENTER_EVIDENCE",
                        },
                    ],
                    "hardcoded_behavior_selections": [],
                },
            ),
        ],
        metrics=[
            RuleMetricExpectation(
                step_id="sealed_variation_points",
                metric_id="OCP-1",
                observation_id="direct_non_injected_count",
                detection_id="OCP-1",
                detection_name="Sealed Variation Points",
                value=2,
                severity="SEVERE",
                mcp_owned=True,
            ),
            RuleMetricExpectation(
                step_id="hardcoded_behavior_selection_count",
                metric_id="OCP-1",
                observation_id="hardcoded_behavior_selection_count",
                detection_id="OCP-1",
                detection_name="Sealed Variation Points",
                value=0,
                severity="COMPLIANT",
                mcp_owned=True,
            ),
            RuleMetricExpectation(
                step_id="untestable_concrete_dependencies",
                metric_id="OCP-2",
                observation_id="untestable_concrete_count",
                detection_id="OCP-2",
                detection_name="Testability",
                value=0,
                severity="COMPLIANT",
                mcp_owned=True,
            ),
            RuleMetricExpectation(
                step_id="testable_concrete_dependencies",
                metric_id="OCP-3",
                observation_id="testable_concrete_count",
                detection_id="OCP-2",
                detection_name="Testability",
                value=0,
                severity="COMPLIANT",
                mcp_owned=True,
            ),
        ],
        final_severity="SEVERE",
    )

    def test_dependency_analysis_is_reused_without_prompt_reserialization(self) -> None:
        started = self._start()

        self.assertEqual(
            [step.step_id for step in started.steps],
            ["analyze_dependencies"],
        )
        dependency_analysis = self.sut.flow_next({
            started.steps[0].instance_id: self.SCENARIO.analysis[0].output,
        })

        self.assertEqual(
            {step.step_id for step in dependency_analysis.steps},
            {"classify_exception"},
        )
        self.assertTrue(all(
            "OCP_USER_DEFAULTS_EVIDENCE" not in step.prompt
            and "OCP_NOTIFICATION_CENTER_EVIDENCE" not in step.prompt
            for step in dependency_analysis.steps
        ))
        exception_step = next(
            step for step in dependency_analysis.steps
            if step.step_id == "classify_exception"
        )
        self.assertIn(
            "no dependencies and no",
            exception_step.prompt,
        )
        self.assertIn(
            "Pure data structures",
            exception_step.prompt,
        )
        self.assertIn(
            "ENTIRE class is exempt",
            exception_step.prompt,
        )

    def test_uses_canonical_rule_detection_and_exception_instructions(self) -> None:
        started = self._start()
        analysis_prompt = started.steps[0].prompt

        self.assertIn("ABSTRACT (protocol-typed and injected)", analysis_prompt)
        self.assertIn("DIRECT_NON_INJECTED", analysis_prompt)
        self.assertIn("has_business_logic", analysis_prompt)
        self.assertIn("has_behavioral_dependencies", analysis_prompt)
        self.assertIn("has_side_effecting_behavior", analysis_prompt)
        self.assertIn("can_substitute_without_modifying_unit", analysis_prompt)
        self.assertIn("can_subclass", analysis_prompt)

        advanced = self.sut.flow_next({
            started.steps[0].instance_id: self.SCENARIO.analysis[0].output,
        })
        exception_prompt = advanced.steps[0].prompt
        self.assertIn("ENTIRE class is exempt from OCP-1 and", exception_prompt)
        self.assertIn("Do NOT flag individual instantiations", exception_prompt)
        self.assertIn("API is not owned by dev", exception_prompt)
        self.assertIn("cannot be subclassed or instantiated", exception_prompt)
        self.assertIn("Test code intentionally uses", exception_prompt)
