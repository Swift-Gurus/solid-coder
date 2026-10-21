"""
solid-name: test_lsp_validation_flow
solid-category: integration-test
solid-spec: [SPEC-039, SPEC-055, SPEC-057]
solid-description: Verifies canonical LSP instructions, typed observations, exception handling, scoring, and audit behavior.
"""

from __future__ import annotations

import json
import sys
import yaml
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
from source.analysis.matching.source_contract_members import SourceContractMembers


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
                step_id="fatal_calls", metric_id="LSP-3", observation_id="fatal_calls",
                detection_id="LSP-3", detection_name="Empty Methods",
                value=1, severity="SEVERE", mcp_owned=True,
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
        started = self.sut.flow_start("lsp", {
            "review_unit": self.unit.model_dump(mode="json"),
            "source_context": self.prepared.source_context.model_dump(mode="json"),
        })
        if started.error is None:
            self.SCENARIO = self.SCENARIO.model_copy(update={"analysis": [RuleAnalysisExpectation(
                step_id="analyze_substitutability",
                output={
                    "has_inheritance": False,
                    "relationship_terms": [self.unit.target.name],
                    "contract_implementations": [
                        {"member": member.identity,
                         "classification": "FATAL" if member.name == "seek" else "MEANINGFUL",
                         "evidence": member.code}
                        for member in self._members(started.run_id).members
                    ],
                },
            )]})
        return started

    def _members(self, run_id):
        event = next(event for event in self._events(run_id)
                     if event.get("event") == "step_completed" and event["step_id"] == "prepare_contract_members")
        return SourceContractMembers.model_validate(event["outputs"])

    def test_exception_makes_metric_decisions_compliant_without_hiding_evidence(self) -> None:
        checkpoint = self._complete_workflow(is_exception=True)
        result = self._rule_result(checkpoint.run_id)
        self.assertFalse(result.exception.is_exception)
        self.assertEqual(result.severity, "SEVERE")
        for metric in result.metrics:
            self.assertEqual(metric.severity, "SEVERE" if metric.observation_id == "fatal_calls" else "COMPLIANT")
            self.assertTrue(metric.additional_info.evidence)

    def test_uses_canonical_rule_detection_and_exception_instructions(self) -> None:
        checkpoint = self._complete_workflow()
        rule = self.SCENARIO.rule_path.read_text()
        reader = RuleInstructionBlockReader()
        authored_workflow = "\n".join(
            step.get("prompt", "") for step in yaml.safe_load(
                (self.PROJECT_ROOT / "workflows/review/rules/lsp/workflow.yaml").read_text()
            )["steps"]
        )
        for metric in self.SCENARIO.metrics:
            if metric.metric_id == "LSP-1":
                continue  # SPEC-064 replaces this inventory/ownership procedure.
            definition = reader.definition(rule, metric.detection_id, metric.detection_name)
            if definition is not None:
                self.assertTrue(definition in authored_workflow if metric.metric_id == "LSP-2"
                                else any(definition in prompt for prompt in checkpoint.prompts))
        prompts = "\n".join(checkpoint.prompts)
        for classification in ["MEANINGFUL", "EMPTY", "FATAL"]:
            self.assertIn(classification, prompts)
        for classification in ["NEW_GUARD", "WEAKENED_POSTCONDITION", "INVARIANT_VIOLATION"]:
            self.assertIn(classification, authored_workflow)
            self.assertNotIn(classification, prompts)
        self.assertNotIn("**Count", prompts)
        self.assertNotIn("**Calculate percentage", prompts)
        self.assertTrue(any(reader.exceptions(rule) in prompt for prompt in checkpoint.prompts))
        self.assertNotIn("if not found -> external", "\n".join(checkpoint.prompts))
        unavailable = self._rule_result(checkpoint.run_id).unavailable_metrics
        self.assertEqual({(item.metric_id, item.observation_id) for item in unavailable},
                         {("LSP-3", "value"), ("LSP-4", "value")})
        self.assertTrue(all("isPlaying" in item.additional_info.evidence for item in unavailable))

    def test_false_inheritance_trigger_skips_repository_relationship_work(self) -> None:
        started = self._start()

        self.assertEqual(
            [step.step_id for step in started.steps],
            ["analyze_substitutability"],
        )
        self.assertIn(
            "one `contract_implementations` entry for each listed member ID",
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

        self.assertEqual([step.step_id for step in measured.steps], ["classify_exception"])
        self.assertTrue(all(
            "LSP_SHARED_ANALYSIS_EVIDENCE" not in step.prompt
            for step in measured.steps
        ))
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
            "classify_relationship_violations",
        }.issubset(skipped), skipped)

    def test_missing_contract_classifications_reject_before_scoring_then_recover(self) -> None:
        self.review_unit = """protocol CatalogServing {
    func load() -> String
    func reset()
}
class Catalog: CatalogServing {
    func load() -> String { "catalog" }
    func reset() { fatalError("Reset is unsupported") }
}
"""
        self.prepared = PrepareReviewOperationFactory().make().execute(PrepareReviewInput(
            target=TextAnalysisSource(
                text=self.review_unit,
                virtual_path=str(self.project_root / "Catalog.swift"),
            ),
        ))
        self.unit = next(unit for unit in self.prepared.units if unit.target.name == "Catalog")
        started = self._start()
        self.assertIsNone(started.error, started.error)
        self.assertEqual([step.step_id for step in started.steps], ["analyze_substitutability"])

        rejected = self.sut.flow_next({
            started.steps[0].instance_id: {
                "has_inheritance": False,
                "relationship_terms": ["Catalog"],
                "contract_implementations": [],
            },
        })

        self.assertEqual(
            [step.step_id for step in rejected.steps],
            ["analyze_substitutability"],
            "Missing implementation classifications must not advance to scoring.",
        )
        self.assertIn("load", rejected.steps[0].rejection_reason)
        self.assertIn("reset", rejected.steps[0].rejection_reason)
        meaningful = {
            "member": next(member.identity for member in self._members(started.run_id).members if member.name == "load"),
            "classification": "MEANINGFUL",
            "evidence": 'func load() -> String { "catalog" }',
        }
        pending = self.sut.flow_next({
            rejected.steps[0].instance_id: {
                "has_inheritance": False,
                "relationship_terms": ["Catalog"],
                "contract_implementations": [meaningful],
            },
        })

        self.assertEqual([step.step_id for step in pending.steps], ["analyze_substitutability"])
        self.assertIn("reset", pending.steps[0].rejection_reason)
        self.assertFalse(any(
            event.get("event") == "step_completed" and event.get("step_id") == "fatal_error_methods"
            for event in self._events(started.run_id)
        ))
        classified = self.sut.flow_next({
            pending.steps[0].instance_id: {
                "has_inheritance": False,
                "relationship_terms": ["Catalog"],
                "contract_implementations": [
                    meaningful,
                    {
                        "member": next(member.identity for member in self._members(started.run_id).members if member.name == "reset"),
                        "classification": "FATAL",
                        "evidence": 'func reset() { fatalError("Reset is unsupported") }',
                    },
                ],
            },
        })
        exception = classified
        self.assertEqual([step.step_id for step in exception.steps], ["classify_exception"])
        completed = self.sut.flow_next({
            exception.steps[0].instance_id: {
                "is_exception": False,
                "additional_info": {
                    "reasoning": "Catalog provides behavior and is not a NoOp object.",
                    "evidence": "load returns a value; reset crashes instead of fulfilling its contract.",
                },
            },
        })

        self.assertEqual(completed.status, "done", completed.error)
        fatal = next(metric for metric in self._rule_result(started.run_id).metrics if metric.metric_id == "LSP-3")
        self.assertEqual(fatal.value, 1)
        self.assertEqual(fatal.severity, "SEVERE")

    def _events(self, run_id: str) -> list[dict[str, object]]:
        return [
            json.loads(line)
            for line in (
                self.project_root / "runs" / run_id / "events.jsonl"
            ).read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
