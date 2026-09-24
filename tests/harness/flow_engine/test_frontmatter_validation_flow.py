"""
solid-name: test_frontmatter_validation_flow
solid-category: integration-test
solid-spec: [SPEC-039, SPEC-055]
solid-description: Verifies file-scoped frontmatter instructions, scalar scoring, metric exclusions, and audited results.
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


class TestFrontmatterValidationFlow(RuleValidationFlowContract):
    __test__ = True
    PROJECT_ROOT = _PROJECT_ROOT
    SCENARIO = RuleValidationScenario(
        workflow_id="frontmatter",
        rule_path=(
            _PROJECT_ROOT
            / "references"
            / "principles"
            / "frontmatter"
            / "rule.md"
        ),
        fixture_path=(
            _PROJECT_ROOT
            / "tests"
            / "principles"
            / "frontmatter"
            / "fixtures"
            / "fixture-1.swift"
        ),
        analysis=[
            RuleAnalysisExpectation(
                step_id="classify_frontmatter_observations",
                output={
                    "observations": [
                        {
                            "classification": "MISSING_FRONTMATTER",
                            "location": "PaymentValidator",
                            "is_exception": False,
                            "reasoning": "The top-level class has no preceding solid-frontmatter block.",
                            "evidence": "class PaymentValidator is preceded only by an import.",
                        },
                    ],
                },
            ),
        ],
        metrics=[
            RuleMetricExpectation(step_id="missing_frontmatter_count", metric_id="FM-1", detection_id="FM-1", detection_name="Missing Frontmatter", value=1, severity="SEVERE", mcp_owned=True),
            RuleMetricExpectation(step_id="name_mismatch_count", metric_id="FM-2", detection_id="FM-2", detection_name="Name Mismatch", value=0, severity="COMPLIANT", mcp_owned=True),
            RuleMetricExpectation(step_id="invalid_category_count", metric_id="FM-3", detection_id="FM-3", detection_name="Invalid Category", value=0, severity="COMPLIANT", mcp_owned=True),
            RuleMetricExpectation(step_id="incorrect_stack_count", metric_id="FM-4", detection_id="FM-4", detection_name="Incorrect Stack", value=0, severity="COMPLIANT", mcp_owned=True),
            RuleMetricExpectation(step_id="bad_description_count", metric_id="FM-5", detection_id="FM-5", detection_name="Bad Description", value=0, severity="COMPLIANT", mcp_owned=True),
        ],
        final_severity="SEVERE",
        rule_scope=RuleScope.FILE,
        has_authored_exceptions=False,
    )

    def test_metric_exclusion_removes_only_the_matching_observation(self) -> None:
        started = self._start()
        observation = {
            **self.SCENARIO.analysis[0].output["observations"][0],
            "is_exception": True,
        }

        exception = self.sut.flow_next({
            started.steps[0].instance_id: {"observations": [observation]},
        })
        completed = self.sut.flow_next({
            exception.steps[0].instance_id: {
                "is_exception": False,
                "additional_info": {
                    "reasoning": "No separate rule-wide exception applies.",
                    "evidence": "The declaration exclusion was recorded on its observation.",
                },
            },
        })

        self.assertEqual(completed.status, "done", completed.error)
        result = self._rule_result(started.run_id)
        self.assertEqual([metric.value for metric in result.metrics], [0, 0, 0, 0, 0])
        self.assertEqual(result.severity, "COMPLIANT")

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
            ["classify_frontmatter_observations"],
        )
        self.assertIn("evidence", rejected.steps[0].rejection_reason)
