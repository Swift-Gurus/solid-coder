"""
solid-name: test_lsp_validation_flow
solid-category: integration-test
solid-spec: [SPEC-039]
solid-description: Verifies canonical LSP instructions, typed observations, exception handling, scoring, and audit behavior.
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


class TestLSPValidationFlow(RuleValidationFlowContract):
    __test__ = True
    PROJECT_ROOT = _PROJECT_ROOT
    SCENARIO = RuleValidationScenario(
        workflow_id="lsp",
        rule_path=_PROJECT_ROOT / "references" / "principles" / "LSP" / "rule.md",
        fixture_path=(
            _PROJECT_ROOT
            / "tests"
            / "principles"
            / "LSP"
            / "fixtures"
            / "fixture-1.swift"
        ),
        analysis=[
            RuleAnalysisExpectation(
                step_id="analyze_substitutability",
                output={
                    "type_checks": [
                        {
                            "expression": "value as? Data",
                            "ownership": "EXTERNAL",
                            "evidence": "LSP_SHARED_ANALYSIS_EVIDENCE",
                        }
                    ],
                    "inheritance": {
                        "has_trigger": False,
                        "relationships": [],
                        "reasoning": "No concrete inheritance is present.",
                        "evidence": "LSP_SHARED_ANALYSIS_EVIDENCE",
                    },
                    "contract_implementations": [
                        {
                            "member": "reset",
                            "classification": "FATAL",
                            "evidence": "LSP_SHARED_ANALYSIS_EVIDENCE",
                        }
                    ],
                },
            )
        ],
        metrics=[
            RuleMetricExpectation(
                step_id="type_checks",
                metric_id="LSP-1",
                detection_id="LSP-1",
                detection_name="Type Check Count",
                value=0,
                severity="COMPLIANT",
            ),
            RuleMetricExpectation(
                step_id="contract_violations",
                metric_id="LSP-2",
                detection_id="LSP-2",
                detection_name="Contract Compliance",
                value=0,
                severity="COMPLIANT",
            ),
            RuleMetricExpectation(
                step_id="fatal_error_methods",
                metric_id="LSP-3",
                detection_id="LSP-3",
                detection_name="Empty Methods",
                value=1,
                severity="SEVERE",
            ),
            RuleMetricExpectation(
                step_id="empty_methods",
                metric_id="LSP-4",
                detection_id="LSP-3",
                detection_name="Empty Methods",
                value=0,
                severity="COMPLIANT",
            ),
        ],
        final_severity="SEVERE",
    )

    def test_trigger_and_contract_analysis_is_shared_by_every_lsp_metric(self) -> None:
        started = self._start()

        self.assertEqual(
            [step.step_id for step in started.steps],
            ["analyze_substitutability"],
        )
        self.assertIn(
            "Only classify contract implementations whose method bodies are present inside the supplied Unit",
            started.steps[0].prompt,
        )
        self.assertIn(
            "Protocol requirements declared without bodies are not implementations",
            started.steps[0].prompt,
        )
        self.assertIn(
            "Protocol conformance is not concrete inheritance",
            started.steps[0].prompt,
        )
        measured = self.sut.flow_next({
            started.steps[0].instance_id: self.SCENARIO.analysis[0].output
        })

        self.assertEqual(
            {step.step_id for step in measured.steps},
            {
                "type_checks",
                "contract_violations",
                "fatal_error_methods",
                "empty_methods",
                "classify_exception",
            },
        )
        self.assertTrue(
            all("LSP_SHARED_ANALYSIS_EVIDENCE" in step.prompt for step in measured.steps)
        )
        contract_prompt = next(
            step.prompt for step in measured.steps
            if step.step_id == "contract_violations"
        )
        self.assertIn("has_trigger", contract_prompt)
        self.assertNotIn("FATAL", contract_prompt)
