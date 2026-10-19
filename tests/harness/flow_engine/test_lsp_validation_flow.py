"""
solid-name: test_lsp_validation_flow
solid-category: integration-test
solid-spec: [SPEC-039, SPEC-055, SPEC-057]
solid-description: Verifies canonical LSP instructions, typed observations, exception handling, scoring, and audit behavior.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_PROJECT_ROOT / "mcp-server"))

from rule_analysis_expectation import RuleAnalysisExpectation  # noqa: E402
from rule_metric_expectation import RuleMetricExpectation  # noqa: E402
from rule_validation_flow_contract import RuleValidationFlowContract  # noqa: E402
from rule_validation_scenario import RuleValidationScenario  # noqa: E402
from rule_instruction_block_reader import RuleInstructionBlockReader
from review.prepare_review_input import PrepareReviewInput
from review.prepare_review_operation_factory import PrepareReviewOperationFactory
from source.text_analysis_source import TextAnalysisSource


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
                    "has_inheritance": False,
                    "relationship_terms": ["MediaPlayer"],
                    "contract_implementations": [
                        {
                            "member": "reset",
                            "classification": "FATAL",
                            "evidence": "LSP_SHARED_ANALYSIS_EVIDENCE",
                        }
                    ],
                },
            ),
            RuleAnalysisExpectation(
                step_id="classify_relationship_violations",
                output={"observations": []},
            ),
        ],
        metrics=[
            RuleMetricExpectation(
                step_id="type_checks",
                metric_id="LSP-1",
                detection_id="LSP-1",
                detection_name="Type Check Count",
                value=0,
                severity="COMPLIANT",
                mcp_owned=True,
            ),
            RuleMetricExpectation(
                step_id="contract_violations",
                metric_id="LSP-2",
                detection_id="LSP-2",
                detection_name="Contract Compliance",
                value=0,
                severity="COMPLIANT",
                mcp_owned=True,
            ),
            RuleMetricExpectation(
                step_id="fatal_error_methods",
                metric_id="LSP-3",
                detection_id="LSP-3",
                detection_name="Empty Methods",
                value=1,
                severity="SEVERE",
                mcp_owned=True,
            ),
            RuleMetricExpectation(
                step_id="empty_methods",
                metric_id="LSP-4",
                detection_id="LSP-3",
                detection_name="Empty Methods",
                value=0,
                severity="COMPLIANT",
                mcp_owned=True,
            ),
        ],
        final_severity="SEVERE",
    )

    def setUp(self) -> None:
        super().setUp()
        self.prepared = PrepareReviewOperationFactory().make().execute(PrepareReviewInput(
            target=TextAnalysisSource(text=self.review_unit, virtual_path=str(self.project_root / "Fixture.swift")),
        ))
        self.unit = next(unit for unit in self.prepared.units if unit.target.name == "LiveStreamPlayer")
        self.review_unit_name = self.unit.target.name

    def _start(self):
        return self.sut.flow_start("lsp", {
            "review_unit": self.unit.model_dump(mode="json"),
            "source_context": self.prepared.source_context.model_dump(mode="json"),
        })

    def test_uses_canonical_rule_detection_and_exception_instructions(self) -> None:
        checkpoint = self._complete_workflow()
        rule = self.SCENARIO.rule_path.read_text()
        reader = RuleInstructionBlockReader()
        for metric in self.SCENARIO.metrics:
            if metric.metric_id == "LSP-1":
                continue  # SPEC-064 replaces this inventory/ownership procedure.
            definition = reader.definition(rule, metric.detection_id, metric.detection_name)
            if definition is not None:
                self.assertTrue(any(definition in prompt for prompt in checkpoint.prompts))
        prompts = "\n".join(checkpoint.prompts)
        for classification in ["NEW_GUARD", "WEAKENED_POSTCONDITION", "INVARIANT_VIOLATION", "MEANINGFUL", "EMPTY", "FATAL"]:
            self.assertIn(classification, prompts)
        self.assertNotIn("**Count", prompts)
        self.assertNotIn("**Calculate percentage", prompts)
        self.assertTrue(any(reader.exceptions(rule) in prompt for prompt in checkpoint.prompts))
        self.assertNotIn("if not found -> external", "\n".join(checkpoint.prompts))
        self.assertEqual(self._rule_result(checkpoint.run_id).unavailable_metrics, [])

    def test_false_inheritance_trigger_skips_repository_relationship_work(self) -> None:
        started = self._start()

        self.assertEqual(
            [step.step_id for step in started.steps],
            ["analyze_substitutability"],
        )
        self.assertIn(
            "only for implementations whose\nbodies are present inside the supplied unit",
            started.steps[0].prompt,
        )
        self.assertIn(
            "Protocol requirements declared\nwithout bodies are not implementations",
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
            [step.step_id for step in measured.steps],
            ["classify_relationship_violations"],
        )
        self.assertTrue(all(
            "LSP_SHARED_ANALYSIS_EVIDENCE" not in step.prompt
            for step in measured.steps
        ))
        self.assertTrue(all(
            "completed repository inspections" in step.prompt
            for step in measured.steps
        ))
        exception = self.sut.flow_next({
            measured.steps[0].instance_id: {"observations": []},
        })
        self.assertEqual(
            [step.step_id for step in exception.steps],
            ["classify_exception"],
        )
        skipped = {
            event["step_id"]
            for event in self._events(started.run_id)
            if event.get("event") == "step_skipped"
        }
        self.assertTrue({
            "prepare_relationship_query",
            "search_relationship_candidates",
            "present_relationship_candidates",
            "select_relationship_candidates",
            "validate_relationship_candidates",
        }.issubset(skipped), skipped)

    def _events(self, run_id: str) -> list[dict[str, object]]:
        return [
            json.loads(line)
            for line in (
                self.project_root / "runs" / run_id / "events.jsonl"
            ).read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
