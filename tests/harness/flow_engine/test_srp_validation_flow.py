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
                step_id="analyze_responsibilities",
                output={
                    "actions": [
                        {
                            "method": method,
                            "action": action,
                            "reasoning": f"{method} has the {action} outcome.",
                            "evidence": f"{method} source body",
                        }
                        for method, action in (
                            ("save", "save"),
                            ("load", "load"),
                            ("invalidate", "invalidate"),
                            ("render", "render"),
                            ("format", "format"),
                            ("present", "present"),
                        )
                    ],
                    "cohesion_groups": [
                        {
                            "methods": ["save", "load", "invalidate"],
                            "variables": ["storage", "cache"],
                            "reasoning": "These methods share data-access state.",
                            "evidence": "storage and cache are used together.",
                        },
                        {
                            "methods": ["render", "format", "present"],
                            "variables": ["template", "formatter"],
                            "reasoning": "These methods produce presentation output.",
                            "evidence": "template and formatter drive rendering.",
                        },
                    ],
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
        analysis = self._start()
        self.assertEqual(
            [step.step_id for step in analysis.steps],
            ["analyze_responsibilities"],
        )
        self.assertNotIn(self.review_unit, analysis.steps[0].prompt)
        self.assertIn(self.review_unit_name, analysis.steps[0].prompt)

        exception = self.sut.flow_next({
            analysis.steps[0].instance_id: self.SCENARIO.analysis[0].output,
        })
        self.assertEqual(
            [step.step_id for step in exception.steps],
            ["classify_exception"],
        )
        self.assertNotIn(self.review_unit, exception.steps[0].prompt)
        self.assertNotIn("Canonical srp fixture evidence", exception.steps[0].prompt)

    def test_rejects_an_observation_without_required_evidence(self) -> None:
        analysis = self._start()
        invalid_output = dict(self.SCENARIO.analysis[0].output)
        invalid_output["actions"] = [
            {
                "method": "save",
                "action": "save",
                "reasoning": "The method persists the supplied data.",
            }
        ]

        rejected = self.sut.flow_next({
            analysis.steps[0].instance_id: invalid_output,
        })

        self.assertEqual(rejected.status, "ready")
        self.assertEqual(
            [step.step_id for step in rejected.steps],
            ["analyze_responsibilities"],
        )
        self.assertIn("evidence", rejected.steps[0].rejection_reason)
