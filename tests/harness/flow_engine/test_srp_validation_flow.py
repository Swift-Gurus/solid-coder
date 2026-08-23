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
                    "analysis": {
                        "actions": [
                            {
                                "method": "save",
                                "action": "persist",
                                "reasoning": "The method stores catalog data.",
                                "evidence": "SRP_SHARED_ANALYSIS_EVIDENCE",
                            }
                        ],
                        "cohesion_groups": [
                            {
                                "methods": ["save", "load"],
                                "variables": ["storage", "cache"],
                                "reasoning": "The methods share data-access state.",
                                "evidence": "SRP_SHARED_ANALYSIS_EVIDENCE",
                            }
                        ],
                        "stakeholders": [
                            {
                                "name": "data-access",
                                "methods": ["save", "load"],
                                "reasoning": "Persistence changes drive these methods.",
                                "evidence": "SRP_SHARED_ANALYSIS_EVIDENCE",
                            }
                        ],
                    }
                },
            )
        ],
        metrics=[
            RuleMetricExpectation(
                step_id="verb_count",
                metric_id="SRP-1",
                detection_id="SRP-1",
                detection_name="Verb Count",
                value=6,
                severity="SEVERE",
            ),
            RuleMetricExpectation(
                step_id="cohesion_groups",
                metric_id="SRP-2",
                detection_id="SRP-2",
                detection_name="Cohesion Groups",
                value=2,
                severity="SEVERE",
            ),
            RuleMetricExpectation(
                step_id="stakeholder_count",
                metric_id="SRP-3",
                detection_id="SRP-3",
                detection_name="Stakeholder Count",
                value=2,
                severity="SEVERE",
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

    def test_responsibility_analysis_is_shared_by_every_srp_metric(self) -> None:
        started = self._start()

        self.assertEqual(
            [step.step_id for step in started.steps],
            ["analyze_responsibilities"],
        )
        measured = self.sut.flow_next({
            started.steps[0].instance_id: self.SCENARIO.analysis[0].output
        })

        self.assertEqual(
            {step.step_id for step in measured.steps},
            {"verb_count", "cohesion_groups", "stakeholder_count", "classify_exception"},
        )
        self.assertTrue(
            all("SRP_SHARED_ANALYSIS_EVIDENCE" in step.prompt for step in measured.steps)
        )
