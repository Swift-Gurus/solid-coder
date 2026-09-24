"""
solid-name: test_code_smells_validation_flow
solid-category: integration-test
solid-spec: [SPEC-039, SPEC-055]
solid-description: Verifies file-scoped applicability, canonical smell instructions, typed observations, scoring, and audit behavior.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_PROJECT_ROOT / "mcp-server"))

from harness.rule_scope import RuleScope  # noqa: E402
from rule_analysis_expectation import RuleAnalysisExpectation  # noqa: E402
from rule_metric_expectation import RuleMetricExpectation  # noqa: E402
from rule_validation_flow_contract import RuleValidationFlowContract  # noqa: E402
from rule_validation_scenario import RuleValidationScenario  # noqa: E402


class TestCodeSmellsValidationFlow(RuleValidationFlowContract):
    __test__ = True
    PROJECT_ROOT = _PROJECT_ROOT
    SCENARIO = RuleValidationScenario(
        workflow_id="code-smells",
        rule_path=(
            _PROJECT_ROOT
            / "references"
            / "principles"
            / "code-smells"
            / "rule.md"
        ),
        fixture_path=(
            _PROJECT_ROOT
            / "tests"
            / "principles"
            / "code-smells"
            / "fixtures"
            / "fixture-1.swift"
        ),
        analysis=[
            RuleAnalysisExpectation(
                step_id="classify_smell_observations",
                output={
                    "observations": [
                        {
                            "classification": "STATIC_LOGIC",
                            "location": "ReportComposer.compose(for:)",
                            "is_exception": False,
                            "reasoning": "The static method branches and transforms rows.",
                            "evidence": "static func compose contains an if and joined transformation.",
                        },
                        {
                            "classification": "TYPE_BOUNDARY",
                            "location": "ReportComposer",
                            "is_exception": False,
                            "reasoning": "ReportComposer is one top-level struct boundary.",
                            "evidence": "Top-level struct ReportComposer declaration.",
                        },
                        {
                            "classification": "TYPE_BOUNDARY",
                            "location": "ReportEnvelope",
                            "is_exception": False,
                            "reasoning": "ReportEnvelope is a second top-level struct boundary.",
                            "evidence": "Top-level struct ReportEnvelope declaration.",
                        },
                        {
                            "classification": "INLINE_TYPE",
                            "location": "ReportComposer.makeSection.InlineSection",
                            "is_exception": False,
                            "reasoning": "InlineSection is declared inside a method body.",
                            "evidence": "struct InlineSection inside makeSection().",
                        },
                    ],
                },
            ),
        ],
        metrics=[
            RuleMetricExpectation(
                step_id="static_logic_count",
                metric_id="CS-1",
                detection_id="CS-1",
                detection_name="Static Logic",
                value=1,
                severity="SEVERE",
                mcp_owned=True,
            ),
            RuleMetricExpectation(
                step_id="class_struct_count",
                metric_id="CS-2",
                detection_id="CS-2",
                detection_name="Multiple Types Per File",
                value=2,
                severity="SEVERE",
                mcp_owned=True,
            ),
            RuleMetricExpectation(
                step_id="inline_type_count",
                metric_id="CS-3",
                detection_id="CS-3",
                detection_name="Inline Type Definition",
                value=1,
                severity="SEVERE",
                mcp_owned=True,
            ),
        ],
        final_severity="SEVERE",
        rule_scope=RuleScope.FILE,
        has_authored_exceptions=False,
    )

    def test_metric_exclusion_removes_only_the_matching_observation(self) -> None:
        started = self._start()
        observations = [
            {
                **observation,
                "is_exception": observation["location"] == "ReportEnvelope",
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
                    "reasoning": "No separate rule-wide exception applies.",
                    "evidence": "The exclusion belongs only to ReportEnvelope.",
                },
            },
        })

        self.assertEqual(completed.status, "done", completed.error)
        result = self._rule_result(started.run_id)
        metrics = {metric.metric_id: metric for metric in result.metrics}
        self.assertEqual(metrics["CS-1"].value, 1)
        self.assertEqual(metrics["CS-2"].value, 1)
        self.assertEqual(metrics["CS-3"].value, 1)
        self.assertEqual(metrics["CS-2"].severity, "COMPLIANT")
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
            ["classify_smell_observations"],
        )
        self.assertIn("evidence", rejected.steps[0].rejection_reason)
