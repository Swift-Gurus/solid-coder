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

from harness.rule_scope import RuleScope
from rule_metric_expectation import RuleMetricExpectation
from rule_validation_flow_contract import RuleValidationFlowContract
from rule_validation_scenario import RuleValidationScenario
from rule_workflow_checkpoint import RuleWorkflowCheckpoint


class TestFrontmatterValidationFlow(RuleValidationFlowContract):
    __test__ = True
    PROJECT_ROOT = _PROJECT_ROOT
    SCENARIO = RuleValidationScenario(
        workflow_id="frontmatter",
        rule_path=(
            _PROJECT_ROOT / "references" / "principles" / "frontmatter" / "rule.md"
        ),
        fixture_path=(
            _PROJECT_ROOT
            / "tests"
            / "principles"
            / "frontmatter"
            / "fixtures"
            / "fixture-1.swift"
        ),
        analysis=[],
        metrics=[
            RuleMetricExpectation(
                step_id="missing_frontmatter_count",
                metric_id="FM-1",
                detection_id="FM-1",
                detection_name="Missing Frontmatter",
                value=1,
                severity="SEVERE",
                mcp_owned=True,
            ),
            RuleMetricExpectation(
                step_id="name_mismatch_count",
                metric_id="FM-2",
                detection_id="FM-2",
                detection_name="Name Mismatch",
                value=0,
                severity="COMPLIANT",
                mcp_owned=True,
            ),
            RuleMetricExpectation(
                step_id="invalid_category_count",
                metric_id="FM-3",
                detection_id="FM-3",
                detection_name="Invalid Category",
                value=0,
                severity="COMPLIANT",
                mcp_owned=True,
            ),
            RuleMetricExpectation(
                step_id="incorrect_stack_count",
                metric_id="FM-4",
                detection_id="FM-4",
                detection_name="Incorrect Stack",
                value=0,
                severity="COMPLIANT",
                mcp_owned=True,
            ),
            RuleMetricExpectation(
                step_id="bad_description_count",
                metric_id="FM-5",
                detection_id="FM-5",
                detection_name="Bad Description",
                value=0,
                severity="COMPLIANT",
                mcp_owned=True,
            ),
        ],
        final_severity="SEVERE",
        rule_scope=RuleScope.FILE,
        has_authored_exceptions=False,
    )

    def _start(self):
        return self.sut.flow_start(
            "frontmatter",
            {
                "review_unit": {
                    "target": {
                        "name": self.review_unit_name,
                        "code": self.review_unit,
                        "source_identity": str(self.project_root / "Unwritten.swift"),
                    }
                }
            },
        )

    def _advance_through_analysis(self):
        result = self._start()
        self.assertEqual(result.status, "done", result.error)
        return RuleWorkflowCheckpoint(
            run_id=result.run_id, result=result, prompts=[], step_ids=[]
        )

    def test_exposes_only_model_owned_steps_and_one_exception(self):
        checkpoint = self._complete_workflow()
        self.assertEqual(checkpoint.step_ids, [])
        self.assertEqual(checkpoint.prompts, [])

    def test_uses_canonical_rule_detection_and_exception_instructions(self):
        self.review_unit = (
            self.PROJECT_ROOT / "tests/principles/frontmatter/fixtures/fixture-2.swift"
        ).read_text()
        ready = self._start()
        self.assertIsNone(ready.error, ready.error)
        self.assertEqual(
            [step.step_id for step in ready.steps], ["classify_descriptions"]
        )
        prompt = ready.steps[0].prompt
        for phrase in [
            "interface level",
            "implementation changed entirely",
            "IMPLEMENTATION_DETAIL",
            "VAGUE",
            "solid-description",
        ]:
            self.assertIn(phrase, prompt)
        self.assertNotIn(self.review_unit, prompt)
        self.assertNotIn("Count each", prompt)

    def test_exception_makes_metric_decisions_compliant_without_hiding_evidence(self):
        checkpoint = self._complete_workflow()
        self.assertFalse(self._rule_result(checkpoint.run_id).exception.is_exception)

    def test_metric_exclusion_is_derived_from_source_visibility(self):
        self.review_unit = "private struct Helper {}"
        completed = self._start()
        self.assertEqual(completed.status, "done", completed.error)
        self.assertEqual(
            [entry.value for entry in self._rule_result(completed.run_id).metrics],
            [0, 0, 0, 0, 0],
        )

    def test_unsupported_source_is_unavailable_without_model_classification(self):
        completed = self.sut.flow_start(
            "frontmatter",
            {
                "review_unit": {
                    "target": {
                        "name": "Unknown",
                        "code": "not parsed",
                        "source_identity": str(self.project_root / "Source.unknown"),
                    }
                }
            },
        )
        self.assertEqual(completed.status, "done", completed.error)
        result = self._rule_result(completed.run_id)
        self.assertEqual(result.metrics, [])
        self.assertEqual(
            {entry.metric_id for entry in result.unavailable_metrics},
            {"FM-1", "FM-2", "FM-3", "FM-4", "FM-5"},
        )
