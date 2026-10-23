"""Validates source-backed Code Smells through the shared rule test contract."""

import json
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_PROJECT_ROOT / "mcp-server"))

from harness.rule_scope import RuleScope
from rule_analysis_expectation import RuleAnalysisExpectation
from rule_metric_expectation import RuleMetricExpectation
from rule_validation_flow_contract import RuleValidationFlowContract
from rule_validation_scenario import RuleValidationScenario
from rule_workflow_checkpoint import RuleWorkflowCheckpoint
from source.analysis.declarations.source_declaration_selection_result import (
    SourceDeclarationSelectionResult,
)

"""
solid-name: TestCodeSmellsValidationFlow
solid-category: integration-test
solid-spec: [SPEC-039, SPEC-066]
solid-description: Verifies source-owned candidate coverage, semantic classification, deterministic scoring, fixed exception audit and recovery against the real bundled Code Smells workflow.
"""


class TestCodeSmellsValidationFlow(RuleValidationFlowContract):
    __test__ = True
    PROJECT_ROOT = _PROJECT_ROOT
    SCENARIO = RuleValidationScenario(
        workflow_id="code-smells",
        rule_path=_PROJECT_ROOT / "references/principles/code-smells/rule.md",
        fixture_path=_PROJECT_ROOT
        / "tests/principles/code-smells/fixtures/fixture-1.swift",
        analysis=[RuleAnalysisExpectation(step_id="classify_declarations", output={})],
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

    def _start(self):
        return self.sut.flow_start(
            "code-smells",
            {
                "review_unit": {
                    "target": {
                        "name": self.review_unit_name,
                        "source_identity": str(self.project_root / "Unwritten.swift"),
                        "code": self.review_unit,
                    }
                }
            },
        )

    def _selection(self, run_id):
        events = [
            json.loads(line)
            for line in (self.project_root / "runs" / run_id / "events.jsonl")
            .read_text()
            .splitlines()
        ]
        event = next(
            event
            for event in events
            if event.get("event") == "step_completed"
            and event["step_id"] == "select_declarations"
        )
        return SourceDeclarationSelectionResult.model_validate(event["outputs"])

    def _response(self, run_id):
        return {
            "file_context": {
                "is_build_dsl": False,
                "additional_info": {
                    "reasoning": "Application source.",
                    "evidence": self.review_unit_name,
                },
            },
            "classifications": [
                {
                    "kind": "independent",
                    "declaration_id": entry.identity,
                    "has_business_logic": entry.unit.name == "compose",
                    "additional_info": {
                        "reasoning": "Independent source declaration.",
                        "evidence": entry.unit.name,
                    },
                }
                for entry in self._selection(run_id).declarations
            ],
        }

    def _advance_through_analysis(self):
        ready = self._start()
        self.assertIsNone(ready.error, ready.error)
        self.assertEqual(
            [step.step_id for step in ready.steps], ["classify_declarations"]
        )
        completed = self.sut.flow_next(
            {ready.steps[0].instance_id: self._response(ready.run_id)}
        )
        self.assertEqual(completed.status, "done", completed.error)
        return RuleWorkflowCheckpoint(
            run_id=ready.run_id,
            result=completed,
            prompts=[step.prompt for step in ready.steps],
            step_ids=[step.step_id for step in ready.steps],
        )

    def test_exposes_only_model_owned_steps_and_one_exception(self):
        checkpoint = self._complete_workflow()
        self.assertEqual(checkpoint.step_ids, ["classify_declarations"])
        self.assertNotIn(self.review_unit, checkpoint.prompts[0])
        self.assertIn(self.review_unit_name, checkpoint.prompts[0])
        self.assertFalse((self.project_root / "Unwritten.swift").exists())

    def test_uses_canonical_rule_detection_and_exception_instructions(self):
        checkpoint = self._complete_workflow()
        prompt = checkpoint.prompts[0]
        for wording in [
            "business logic",
            "build-system DSL",
            "implemented_contract",
            "supporting_helper",
            "cohesive_contract",
            "consumes",
        ]:
            self.assertIn(wording, prompt)
        self.assertNotIn("Count static", prompt)
        self.assertNotIn("Count top-level", prompt)
        self.assertNotIn("classify_exception", checkpoint.step_ids)

    def test_exception_makes_metric_decisions_compliant_without_hiding_evidence(self):
        # This rule has authored metric exclusions, not a model-selected whole-rule exemption.
        checkpoint = self._complete_workflow()
        exception = self._rule_result(checkpoint.run_id).exception
        self.assertFalse(exception.is_exception)
        self.assertTrue(exception.additional_info.evidence)
        self.assertTrue(exception.additional_info.reasoning)

    def test_rejects_missing_evidence_then_accepts_complete_correction(self):
        ready = self._start()
        output = self._response(ready.run_id)
        del output["classifications"][0]["additional_info"]["evidence"]
        pending = self.sut.flow_next({ready.steps[0].instance_id: output})
        self.assertEqual(pending.status, "ready")
        self.assertIn("evidence", pending.steps[0].rejection_reason)
        done = self.sut.flow_next(
            {pending.steps[0].instance_id: self._response(ready.run_id)}
        )
        self.assertEqual(done.status, "done", done.error)

    def test_incomplete_identity_coverage_reopens_classifier_and_corrected_submission_scores(
        self,
    ):
        ready = self._start()
        output = self._response(ready.run_id)
        output["classifications"].pop()
        pending = self.sut.flow_next({ready.steps[0].instance_id: output})
        self.assertEqual(pending.status, "ready", pending.error)
        self.assertEqual(
            [step.step_id for step in pending.steps], ["classify_declarations"]
        )
        self.assertIn("missing", pending.steps[0].rejection_reason)
        self.assertIn("complete replacement", pending.steps[0].rejection_reason)
        self.assertFalse(
            (
                self.project_root / "runs" / ready.run_id / "results/review/result.json"
            ).exists()
        )
        done = self.sut.flow_next(
            {pending.steps[0].instance_id: self._response(ready.run_id)}
        )
        self.assertEqual(done.status, "done", done.error)
        self.assertEqual(
            [entry.value for entry in self._rule_result(ready.run_id).metrics],
            [1, 2, 1],
        )

    def test_build_dsl_excludes_static_logic_and_local_types_not_independent_boundaries(
        self,
    ):
        ready = self._start()
        output = self._response(ready.run_id)
        output["file_context"]["is_build_dsl"] = True
        done = self.sut.flow_next({ready.steps[0].instance_id: output})
        self.assertEqual(done.status, "done", done.error)
        self.assertEqual(
            [entry.value for entry in self._rule_result(ready.run_id).metrics],
            [0, 2, 0],
        )

    def test_unsupported_source_remains_unavailable_without_model_classification(self):
        ready = self.sut.flow_start(
            "code-smells",
            {
                "review_unit": {
                    "target": {
                        "name": "Unsupported",
                        "source_identity": str(self.project_root / "Source.unknown"),
                        "code": "not parsed",
                    }
                }
            },
        )
        self.assertEqual(ready.status, "done", ready.error)
        result = self._rule_result(ready.run_id)
        self.assertEqual(result.metrics, [])
        self.assertEqual(
            {entry.metric_id for entry in result.unavailable_metrics},
            {"CS-1", "CS-2", "CS-3"},
        )
