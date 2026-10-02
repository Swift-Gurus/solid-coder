"""
solid-name: test_srp_validation_flow
solid-category: integration-test
solid-spec: [SPEC-039]
solid-description: Verifies packaged SRP observation, validation, scoring, and audit behavior through the flow engine.
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


class TestSRPValidationFlow(RuleValidationFlowContract):
    __test__ = True
    PROJECT_ROOT = _PROJECT_ROOT
    SCENARIO = RuleValidationScenario(
        workflow_id="srp",
        rule_path=_PROJECT_ROOT / "references" / "principles" / "SRP" / "rule.md",
        fixture_path=(
            _PROJECT_ROOT
            / "tests"
            / "principles"
            / "SRP"
            / "fixtures"
            / "fixture-1.swift"
        ),
        analysis=[
            RuleAnalysisExpectation(
                step_id="classify_actions",
                output={
                    "actions": [
                        {
                            "method": "init",
                            "action": "initialize",
                            "is_lifecycle": True,
                            "reasoning": "The initializer stores injected dependencies.",
                            "evidence": "self.storage = storage; self.cache = cache",
                        },
                        *[
                            {
                                "method": method,
                                "action": method,
                                "is_lifecycle": False,
                                "reasoning": f"{method} has an independently meaningful outcome.",
                                "evidence": f"{method} source body",
                            }
                            for method in (
                                "save", "load", "invalidate", "render", "format", "present",
                            )
                        ],
                    ],
                },
            ),
            RuleAnalysisExpectation(
                step_id="classify_variable_usage",
                output={
                    "method_variable_usage": [
                        {
                            "method": "init",
                            "variables": ["storage", "cache", "template", "formatter"],
                            "is_lifecycle": True,
                            "is_orchestrator": False,
                            "reasoning": "Initialization connects all fields but is lifecycle behavior.",
                            "evidence": "The initializer assigns all four stored properties.",
                        },
                        *[
                            {
                                "method": method,
                                "variables": ["storage", "cache"],
                                "is_lifecycle": False,
                                "is_orchestrator": False,
                                "reasoning": "Both fields contribute to one data-access outcome.",
                                "evidence": f"{method} directly accesses storage and cache.",
                            }
                            for method in ("save", "load", "invalidate")
                        ],
                        {
                            "method": "render",
                            "variables": ["template", "formatter"],
                            "is_lifecycle": False,
                            "is_orchestrator": False,
                            "reasoning": "Both fields produce one rendered result.",
                            "evidence": "template.replacingOccurrences uses formatter.string",
                        },
                        {
                            "method": "format",
                            "variables": ["formatter"],
                            "is_lifecycle": False,
                            "is_orchestrator": False,
                            "reasoning": "The method configures and uses the formatter.",
                            "evidence": "formatter.minimumFractionDigits; formatter.string",
                        },
                        {
                            "method": "present",
                            "variables": ["template"],
                            "is_lifecycle": False,
                            "is_orchestrator": False,
                            "reasoning": "The template renders each displayed item.",
                            "evidence": "items.map { template.replacingOccurrences(...) }",
                        },
                    ],
                },
            ),
            RuleAnalysisExpectation(
                step_id="classify_stakeholders",
                output={
                    "stakeholders": [
                        {
                            "stakeholder": "data access",
                            "methods": ["save", "load", "invalidate"],
                            "reasoning": "Persistence changes drive these methods.",
                            "evidence": "UserDefaults and cache behavior.",
                        },
                        {
                            "stakeholder": "presentation",
                            "methods": ["render", "format", "present"],
                            "reasoning": "Presentation changes drive these methods.",
                            "evidence": "Template and number formatting behavior.",
                        },
                    ],
                },
            ),
        ],
        metrics=[
            RuleMetricExpectation(
                step_id="verb_count",
                metric_id="SRP-1",
                detection_id="SRP-1",
                detection_name="Verb Count",
                value=6,
                severity="SEVERE",
                mcp_owned=True,
            ),
            RuleMetricExpectation(
                step_id="cohesion_groups",
                metric_id="SRP-2",
                detection_id="SRP-2",
                detection_name="Cohesion Groups",
                value=2,
                severity="SEVERE",
                mcp_owned=True,
            ),
            RuleMetricExpectation(
                step_id="stakeholder_count",
                metric_id="SRP-3",
                detection_id="SRP-3",
                detection_name="Stakeholder Count",
                value=2,
                severity="SEVERE",
                mcp_owned=True,
            ),
        ],
        final_severity="SEVERE",
        included_unit_kinds=[
            "class",
            "struct",
            "enum",
            "extension",
            "actor",
            "function",
        ],
    )

    def test_analysis_is_reused_without_prompt_reserialization(self) -> None:
        checkpoint = self._advance_through_analysis()
        prompts = "\n".join(checkpoint.prompts)

        self.assertEqual(
            [step.step_id for step in checkpoint.result.steps],
            ["classify_exception"],
        )
        self.assertNotIn(self.review_unit, prompts)
        self.assertIn(self.review_unit_name, prompts)
        self.assertNotIn("Both fields produce one rendered result.", prompts)

    def test_uses_canonical_rule_detection_and_exception_instructions(self) -> None:
        checkpoint = self._advance_through_analysis()
        prompts = "\n".join(checkpoint.prompts)

        self.assertIn("single action verb, not a description", prompts)
        self.assertIn("initializer,", prompts)
        self.assertIn("deinitializer, or factory method", prompts)
        self.assertIn("every instance variable it directly uses", prompts)
        self.assertIn("is_orchestrator", prompts)
        self.assertIn("distinct stakeholders", prompts)
        self.assertIn("Every stored property and initializer parameter is protocol-typed", prompts)
        self.assertIn("pure delegation without business logic", prompts)
        self.assertIn("every dependency is", prompts)
        self.assertIn("injected through its initializer", prompts)

    def test_rejects_an_observation_without_required_evidence(self) -> None:
        analysis = self._start()

        rejected = self.sut.flow_next({
            analysis.steps[0].instance_id: {
                "actions": [
                    {
                        "method": "save",
                        "action": "save",
                        "is_lifecycle": False,
                        "reasoning": "The method persists the supplied data.",
                    }
                ],
            },
        })

        self.assertEqual(rejected.status, "ready")
        self.assertEqual(
            [step.step_id for step in rejected.steps],
            ["classify_actions", "classify_variable_usage", "classify_stakeholders"],
        )
        self.assertIn("evidence", rejected.steps[0].rejection_reason)
