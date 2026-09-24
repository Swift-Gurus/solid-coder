"""Tests the unit-scoped DRY workflow and MCP-owned source comparison."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from harness.flow_run_orchestrator_factory import FlowRunOrchestratorFactory
from harness.project_context import ProjectDirectory
from harness.rule_applicability_context import RuleApplicabilityContext
from harness.rule_review_result import RuleReviewResult
from harness.runs_base_dir_resolver import RunsBaseDirResolver
from harness.static_session_id_reader import StaticSessionIdReader
from rule_instruction_block_reader import RuleInstructionBlockReader
from review.normalized_review_unit import NormalizedReviewUnit
from source.file_analysis_source import FileAnalysisSource
from source.text_analysis_source import TextAnalysisSource
from source.prepare_search_targets_input import PrepareSearchTargetsInput
from source.prepare_search_targets_operation_factory import (
    PrepareSearchTargetsOperationFactory,
)
from source.search_target_granularity import SearchTargetGranularity
from source.source_search_target import SourceSearchTarget
from source.source_operation_registrations_factory import (
    SourceOperationRegistrationsFactory,
)


_PROJECT_ROOT = Path(__file__).resolve().parents[3]


"""
solid-name: TestDryValidationFlow
solid-category: integration-test
solid-spec: [SPEC-039, SPEC-040, SPEC-056]
solid-description: Proves DRY local analysis, typed repository comparison, canonical metrics, audit events, and MCP scoring.
"""
class TestDryValidationFlow(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project_root = Path(temporary.name)
        self.project_directory = ProjectDirectory(path=self.project_root)
        self.run_root = self.project_root / ".solid-coder" / "runs"
        self.current_path = self.project_root / "Current.swift"
        self.current_content = (
            _PROJECT_ROOT / "tests/principles/DRY/fixtures/fixture-1.swift"
        ).read_text(encoding="utf-8")
        self.current_path.write_text(self.current_content, encoding="utf-8")
        (self.project_root / "SharedTaxFormatter.swift").write_text(
            "struct SharedTaxFormatter { func formatTax() {} }\n",
            encoding="utf-8",
        )
        self.engine = FlowRunOrchestratorFactory(
            base_dir_resolver=RunsBaseDirResolver(
                project_dir_fn=lambda: self.project_root / ".solid-coder"
            ),
            plugin_root=_PROJECT_ROOT,
            session_reader=StaticSessionIdReader("dry-flow-test"),
            operation_registrations=SourceOperationRegistrationsFactory(
                project_directory=self.project_directory,
            ).make(),
        ).build()

    def test_executes_local_and_external_lanes_before_mcp_scoring(self) -> None:
        started = self.engine.flow_start("dry", self._parameters())

        self.assertIsNone(started.error, started.error)
        self.assertEqual(
            {step.step_id for step in started.steps},
            {"generate_terms"},
        )
        selection = self.engine.flow_next({
            step.instance_id: self._initial_output(
                step.step_id,
                "SharedTaxFormatter",
            )
            for step in started.steps
        })

        self.assertEqual(len(selection.steps), 1)
        selection_prompt = selection.steps[0].prompt
        self.assertIn("SharedTaxFormatter", selection_prompt)
        self.assertNotIn("struct SharedTaxFormatter", selection_prompt)
        inspection = self.engine.flow_next({
            selection.steps[0].instance_id: self._shared_formatter_dispositions()
        })
        self.assertEqual(len(inspection.steps), 1)
        inspection_prompt = inspection.steps[0].prompt
        self.assertIn(str(self.project_root / "SharedTaxFormatter.swift"), inspection_prompt)
        self.assertNotIn("struct SharedTaxFormatter", inspection_prompt)
        self.assertNotIn("struct PayrollLedger", inspection_prompt)
        classified = self.engine.flow_next({
            inspection.steps[0].instance_id: self._inspection_output()
        })
        self.assertEqual(len(classified.steps), 1)
        candidate_prompt = classified.steps[0].prompt
        self.assertIn("PayrollLedger", candidate_prompt)
        self.assertIn("completed source inspection", candidate_prompt)
        self.assertNotIn("struct SharedTaxFormatter", candidate_prompt)
        self.assertNotIn("struct PayrollLedger", candidate_prompt)
        self.assertEqual(
            candidate_prompt.count("Return only one JSON object matching this schema"),
            1,
        )
        target_analysis = self.engine.flow_next({
            classified.steps[0].instance_id: self._candidate_assessment()
        })

        self.assertEqual(
            [step.step_id for step in target_analysis.steps],
            ["analyze_target_patterns"],
        )
        exception = self.engine.flow_next({
            target_analysis.steps[0].instance_id: self._target_analysis_output()
        })
        self.assertEqual(
            [step.step_id for step in exception.steps],
            ["classify_exception"],
        )
        completed = self.engine.flow_next({
            exception.steps[0].instance_id: self._exception_output()
        })

        self.assertEqual(completed.status, "done")
        result = self._result(started.run_id)
        self.assertEqual(result.workflow_id, "dry")
        self.assertEqual(
            [metric.metric_id for metric in result.metrics],
            ["DRY-1", "DRY-2", "DRY-2", "DRY-3"],
        )
        self.assertEqual([metric.value for metric in result.metrics], [1, 0, 2, 1])
        self.assertEqual(result.severity, "SEVERE")
        self.assertEqual(result.scoring_authority, "mcp")
        self._assert_operation_events(started.run_id)

    def test_embeds_canonical_detection_and_exception_instructions(self) -> None:
        started = self.engine.flow_start("dry", self._parameters())
        selection = self.engine.flow_next({
            step.instance_id: self._initial_output(
                step.step_id,
                "SharedTaxFormatter",
            )
            for step in started.steps
        })
        inspection = self.engine.flow_next({
            selection.steps[0].instance_id: self._shared_formatter_dispositions()
        })
        classified = self.engine.flow_next({
            inspection.steps[0].instance_id: self._inspection_output()
        })
        target_analysis = self.engine.flow_next({
            classified.steps[0].instance_id: self._candidate_assessment()
        })
        exception = self.engine.flow_next({
            target_analysis.steps[0].instance_id: self._target_analysis_output()
        })
        rule = (_PROJECT_ROOT / "references/principles/DRY/rule.md").read_text()
        reader = RuleInstructionBlockReader()

        self.assertIn(
            "EXACT — existing code covers 100% of the need",
            classified.steps[0].prompt,
        )
        self.assertIn(
            reader.detection(rule, "DRY-2", "Inlined Duplication"),
            target_analysis.steps[0].prompt,
        )
        self.assertIn(
            reader.detection(rule, "DRY-3", "Missing Abstraction"),
            target_analysis.steps[0].prompt,
        )
        self.assertIn(reader.exceptions(rule), exception.steps[0].prompt)

    def test_dry2_uses_visible_source_without_reserializing_it(self) -> None:
        (self.project_root / "SharedTaxFormatter.swift").unlink()
        started = self.engine.flow_start("dry", self._parameters())
        selection = self.engine.flow_next({
            step.instance_id: self._initial_output(
                step.step_id,
                "NoRepositoryCandidate",
            )
            for step in started.steps
        })
        target_analysis = self.engine.flow_next({
            selection.steps[0].instance_id: {"dispositions": []}
        })

        self.assertIsNone(target_analysis.error, target_analysis.error)
        duplicate_prompt = target_analysis.steps[0].prompt
        self.assertIn("PayrollLedger", duplicate_prompt)
        self.assertNotIn("func grossWages", duplicate_prompt)
        self.assertNotIn("'code':", duplicate_prompt)
        self.assertNotIn("func reimbursements", duplicate_prompt)
        self.assertIn("within-unit duplication", duplicate_prompt.lower())
        self.assertNotIn("repository candidate", duplicate_prompt.lower())

    def test_term_generation_requires_individual_lexical_words(self) -> None:
        started = self.engine.flow_start("dry", self._parameters())

        self.assertEqual(len(started.steps), 1)
        self.assertIn("exactly one lexical word", started.steps[0].prompt)
        self.assertIn(
            "return `remote`, `resource`, and `loader`",
            started.steps[0].prompt,
        )

    def test_search_requires_summary_selection_before_source_inspection(self) -> None:
        started = self.engine.flow_start("dry", self._parameters())

        selection = self.engine.flow_next({
            started.steps[0].instance_id: {
                "generated_terms": ["SharedTaxFormatter"],
            }
        })

        self.assertEqual([step.step_id for step in selection.steps], ["select_candidates"])
        prompt = selection.steps[0].prompt
        self.assertIn("SharedTaxFormatter", prompt)
        self.assertIn("No solid-description frontmatter.", prompt)
        self.assertIn(str(self.project_root / "SharedTaxFormatter.swift"), prompt)
        self.assertNotIn("struct SharedTaxFormatter", prompt)
        self.assertIn("Account for every repository candidate", prompt)
        self.assertIn("Here is what we found:", prompt)
        self.assertIn("candidate_id: candidate-1", prompt)
        self.assertIn("unit: SharedTaxFormatter", prompt)
        self.assertIn("description: No solid-description frontmatter.", prompt)
        self.assertNotIn("source_identity", prompt)
        self.assertNotIn("unit_identity", prompt)
        self.assertNotIn("content_sha256", prompt)
        self.assertNotIn("matches", prompt)

    def test_classifies_only_candidates_selected_for_llm_file_inspection(self) -> None:
        started = self.engine.flow_start("dry", self._parameters())
        selection = self.engine.flow_next({
            started.steps[0].instance_id: {
                "generated_terms": ["SharedTaxFormatter"],
            }
        })

        inspection = self.engine.flow_next({
            selection.steps[0].instance_id: self._shared_formatter_dispositions()
        })

        self.assertEqual(len(inspection.steps), 1)
        self.assertTrue(inspection.steps[0].step_id.endswith("inspect_candidate"))
        inspection_prompt = inspection.steps[0].prompt
        self.assertIn(str(self.project_root / "SharedTaxFormatter.swift"), inspection_prompt)
        self.assertIn("read the selected file", inspection_prompt.lower())
        self.assertNotIn("struct SharedTaxFormatter", inspection_prompt)
        classification = self.engine.flow_next({
            inspection.steps[0].instance_id: self._inspection_output()
        })

        self.assertEqual(len(classification.steps), 1)
        prompt = classification.steps[0].prompt
        self.assertTrue(classification.steps[0].step_id.endswith("classify_candidate"))
        self.assertIn("NOT_SUITABLE", prompt)
        self.assertIn("NOT_DUPLICATE", prompt)
        self.assertIn(
            "A conformer is not a reusable replacement for its protocol",
            prompt,
        )
        self.assertIn(
            "Choose IDENTICAL or STRUCTURAL only when the completed inspection cites executable statements",
            prompt,
        )
        self.assertIn(
            "Similar names, responsibilities, declarations, or signatures are never implementation duplication",
            prompt,
        )

    def test_rejects_partial_candidate_dispositions_with_replacement_guidance(self) -> None:
        started = self.engine.flow_start("dry", self._parameters())
        selection = self.engine.flow_next({
            started.steps[0].instance_id: {
                "generated_terms": ["SharedTaxFormatter"],
            }
        })

        rejected = self.engine.flow_next({
            selection.steps[0].instance_id: {"dispositions": []}
        })

        self.assertEqual(rejected.status, "ready")
        self.assertEqual(len(rejected.steps), 1)
        retry = rejected.steps[0]
        self.assertEqual(retry.step_id, "select_candidates")
        self.assertIn("missing candidate IDs", retry.rejection_reason)
        self.assertIn("candidate-1", retry.rejection_reason)
        self.assertIn("complete replacement", retry.rejection_reason)

        inspection = self.engine.flow_next({
            retry.instance_id: self._shared_formatter_dispositions()
        })

        self.assertEqual(len(inspection.steps), 1)
        self.assertTrue(inspection.steps[0].step_id.endswith("inspect_candidate"))

    def test_inspects_each_selected_candidate_before_classification(self) -> None:
        started = self.engine.flow_start("dry", self._parameters())
        selection = self.engine.flow_next({
            started.steps[0].instance_id: {
                "generated_terms": ["SharedTaxFormatter"],
            }
        })

        inspection = self.engine.flow_next({
            selection.steps[0].instance_id: self._shared_formatter_dispositions()
        })

        self.assertEqual(len(inspection.steps), 1)
        self.assertTrue(inspection.steps[0].step_id.endswith("inspect_candidate"))
        self.assertIn(
            str(self.project_root / "SharedTaxFormatter.swift"),
            inspection.steps[0].prompt,
        )
        self.assertIn("normal file-reading tool", inspection.steps[0].prompt)

        classification = self.engine.flow_next({
            inspection.steps[0].instance_id: {
                "reasoning": "The candidate contains shared formatting behavior.",
                "evidence": "SharedTaxFormatter.swift contains formatTax().",
            }
        })

        self.assertEqual(len(classification.steps), 1)
        self.assertTrue(classification.steps[0].step_id.endswith("classify_candidate"))
        self.assertIn("completed source inspection", classification.steps[0].prompt)
        self.assertIn("SharedTaxFormatter", classification.steps[0].prompt)
        self.assertNotIn(
            "SharedTaxFormatter.swift contains formatTax()",
            classification.steps[0].prompt,
        )
        self.assertIn("previously submitted", classification.steps[0].prompt)

    def test_compliant_fixture_publishes_zero_metrics(self) -> None:
        self.current_content = (
            _PROJECT_ROOT / "tests/principles/DRY/fixtures/fixture-2.swift"
        ).read_text(encoding="utf-8")
        self.current_path.write_text(self.current_content, encoding="utf-8")
        (self.project_root / "SharedTaxFormatter.swift").unlink()
        started = self.engine.flow_start("dry", self._parameters())
        selection = self.engine.flow_next({
            started.steps[0].instance_id: self._initial_output(
                started.steps[0].step_id,
                "NoRepositoryCandidate",
            )
        })
        target_analysis = self.engine.flow_next({
            selection.steps[0].instance_id: {"dispositions": []}
        })

        exception = self.engine.flow_next({
            target_analysis.steps[0].instance_id: self._empty_target_analysis_output()
        })
        completed = self.engine.flow_next({
            exception.steps[0].instance_id: self._exception_output()
        })

        self.assertEqual(completed.status, "done")
        result = self._result(started.run_id)
        self.assertEqual([metric.value for metric in result.metrics], [0, 0, 0, 0])
        self.assertEqual(result.severity, "COMPLIANT")
        self.assertFalse(result.exception.is_exception)

    def test_exception_preserves_observations_and_makes_result_compliant(self) -> None:
        started = self.engine.flow_start("dry", self._parameters())
        selection = self.engine.flow_next({
            started.steps[0].instance_id: self._initial_output(
                started.steps[0].step_id,
                "SharedTaxFormatter",
            )
        })
        inspection = self.engine.flow_next({
            selection.steps[0].instance_id: self._shared_formatter_dispositions()
        })
        classified = self.engine.flow_next({
            inspection.steps[0].instance_id: self._inspection_output()
        })
        target_analysis = self.engine.flow_next({
            classified.steps[0].instance_id: self._candidate_assessment()
        })
        exception = self.engine.flow_next({
            target_analysis.steps[0].instance_id: self._target_analysis_output()
        })
        completed = self.engine.flow_next({
            exception.steps[0].instance_id: self._exception_output(
                is_exception=True,
            )
        })

        self.assertEqual(completed.status, "done")
        result = self._result(started.run_id)
        self.assertTrue(result.exception.is_exception)
        self.assertEqual([metric.value for metric in result.metrics], [1, 0, 2, 1])
        self.assertEqual(
            [metric.severity for metric in result.metrics],
            ["COMPLIANT", "COMPLIANT", "COMPLIANT", "COMPLIANT"],
        )
        self.assertEqual(result.severity, "COMPLIANT")

    def test_classifies_proposed_sibling_and_cross_file_candidates(self) -> None:
        (self.project_root / "SharedTaxFormatter.swift").unlink()
        current = PrepareSearchTargetsOperationFactory().make().execute(
            PrepareSearchTargetsInput(
                source=TextAnalysisSource(
                    text=(
                        "struct FirstFormatter { func formatProfile() {} }\n"
                        "struct SiblingFormatter { func formatProfile() {} }"
                    ),
                    virtual_path=str(self.current_path),
                ),
                granularity=SearchTargetGranularity.UNIT,
            )
        )
        proposed_path = self.project_root / "ProposedFormatter.swift"
        proposed_path.write_text(
            "struct StaleFormatter { func unrelated() {} }",
            encoding="utf-8",
        )
        proposed = PrepareSearchTargetsOperationFactory().make().execute(
            PrepareSearchTargetsInput(
                source=TextAnalysisSource(
                    text=(
                        "struct ProposedFormatter { "
                        "func formatProfile() {} }"
                    ),
                    virtual_path=str(proposed_path),
                ),
                granularity=SearchTargetGranularity.UNIT,
            )
        )
        reviewed = next(
            target for target in current.targets
            if target.name == "FirstFormatter"
        )
        started = self.engine.flow_start("dry", {
            "review_unit": self._normalized_unit(reviewed).model_dump(
                mode="json"
            ),
            "source_context": {
                "sources": [
                    current.snapshot.model_dump(mode="json"),
                    proposed.snapshot.model_dump(mode="json"),
                ],
            },
        })

        selection = self.engine.flow_next({
            started.steps[0].instance_id: {
                "generated_terms": ["formatProfile"],
            }
        })

        self.assertEqual(len(selection.steps), 1)
        self.assertIn("SiblingFormatter", selection.steps[0].prompt)
        self.assertIn("ProposedFormatter", selection.steps[0].prompt)
        self.assertNotIn("struct SiblingFormatter", selection.steps[0].prompt)
        inspection = self.engine.flow_next({
            selection.steps[0].instance_id: {
                "dispositions": self._inspect_dispositions(2)
            }
        })

        self.assertEqual(len(inspection.steps), 2)
        prompts = "\n".join(step.prompt for step in inspection.steps)
        self.assertIn(str(self.current_path), prompts)
        self.assertIn(str(proposed_path), prompts)
        self.assertNotIn("struct SiblingFormatter", prompts)
        self.assertNotIn("struct ProposedFormatter", prompts)
        self.assertNotIn("struct StaleFormatter", prompts)

    def test_differently_named_existing_protocol_produces_reuse_miss(self) -> None:
        scenario = (
            _PROJECT_ROOT
            / "tests"
            / "principles"
            / "DRY"
            / "repository-scenarios"
            / "exact-protocol-reuse"
        )
        self.current_content = (scenario / "reviewed.swift").read_text(
            encoding="utf-8"
        )
        self.current_path.write_text(self.current_content, encoding="utf-8")
        (self.project_root / "SharedTaxFormatter.swift").unlink()
        (self.project_root / "RemoteContentLoading.swift").write_text(
            (scenario / "existing.swift").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        started = self.engine.flow_start("dry", self._parameters())
        selection = self.engine.flow_next({
            started.steps[0].instance_id: {
                "generated_terms": ["resource"],
            }
        })

        self.assertEqual(len(selection.steps), 1)
        self.assertIn("RemoteContentLoading", selection.steps[0].prompt)
        self.assertNotIn("protocol RemoteContentLoading", selection.steps[0].prompt)
        inspection = self.engine.flow_next({
            selection.steps[0].instance_id: {
                "dispositions": self._inspect_dispositions(1)
            }
        })
        self.assertEqual(len(inspection.steps), 1)
        self.assertIn(
            str(self.project_root / "RemoteContentLoading.swift"),
            inspection.steps[0].prompt,
        )
        self.assertNotIn("protocol RemoteContentLoading", inspection.steps[0].prompt)
        classified = self.engine.flow_next({
            inspection.steps[0].instance_id: self._inspection_output()
        })
        self.assertEqual(len(classified.steps), 1)
        self.assertIn("NetworkResourceFetching", classified.steps[0].prompt)
        self.assertNotIn("protocol NetworkResourceFetching", classified.steps[0].prompt)
        self.assertNotIn("protocol RemoteContentLoading", classified.steps[0].prompt)
        target_analysis = self.engine.flow_next({
            classified.steps[0].instance_id: self._candidate_assessment(
                self.project_root / "RemoteContentLoading.swift"
            )
        })
        exception = self.engine.flow_next({
            target_analysis.steps[0].instance_id: self._empty_target_analysis_output()
        })
        completed = self.engine.flow_next({
            exception.steps[0].instance_id: self._exception_output()
        })

        self.assertEqual(completed.status, "done")
        result = self._result(started.run_id)
        self.assertEqual([metric.value for metric in result.metrics], [1, 0, 0, 0])
        self.assertEqual(
            [metric.severity for metric in result.metrics],
            ["SEVERE", "COMPLIANT", "COMPLIANT", "COMPLIANT"],
        )
        self.assertEqual(result.severity, "SEVERE")

    def _parameters(self) -> dict[str, object]:
        prepared = PrepareSearchTargetsOperationFactory().make().execute(
            PrepareSearchTargetsInput(
                source=FileAnalysisSource(path=self.current_path),
                granularity=SearchTargetGranularity.UNIT,
            )
        )
        self.assertEqual(len(prepared.targets), 1)
        return {
            "review_unit": self._normalized_unit(
                prepared.targets[0]
            ).model_dump(mode="json"),
            "source_context": {
                "sources": [prepared.snapshot.model_dump(mode="json")],
            },
        }

    @staticmethod
    def _normalized_unit(
        target: SourceSearchTarget,
    ) -> NormalizedReviewUnit:
        return NormalizedReviewUnit(
            target=target,
            applicability=RuleApplicabilityContext(
                file_extension=".swift",
                unit_kind=target.kind,
                tags=[],
            ),
            tag_evidence=[],
        )

    @staticmethod
    def _initial_output(
        step_id: str,
        generated_term: str,
    ) -> dict[str, object]:
        return {"generated_terms": [generated_term]}

    def _candidate_assessment(
        self,
        location: Path | None = None,
    ) -> dict[str, object]:
        return {
            "assessment": {
                "candidate_id": "candidate-1",
                "location": str(
                    location or self.project_root / "SharedTaxFormatter.swift"
                ),
                "reuse": {
                    "classification": "EXACT",
                    "is_exception": False,
                    "reasoning": "The candidate covers the complete responsibility.",
                    "evidence": "Both units expose the same responsibility.",
                },
                "duplication": {
                    "classification": "SIMILAR",
                    "is_exception": False,
                    "reasoning": "No duplicated implemented sequence is established.",
                    "evidence": "The comparison alone does not prove copied logic.",
                },
            }
        }

    @staticmethod
    def _inspection_output() -> dict[str, str]:
        return {
            "reasoning": "The candidate contains the described behavior.",
            "evidence": "The inspected candidate contains relevant executable statements.",
        }

    def _shared_formatter_dispositions(self) -> dict[str, object]:
        return {
            "dispositions": self._inspect_dispositions(1)
        }

    @staticmethod
    def _inspect_dispositions(count: int) -> list[dict[str, str]]:
        return [
            {
                "candidate_id": f"candidate-{index}",
                "disposition": "INSPECT",
                "reasoning": "The summary indicates equivalent formatting behavior.",
                "evidence": "The candidate description names formatting behavior.",
            }
            for index in range(1, count + 1)
        ]

    @staticmethod
    def _target_analysis_output() -> dict[str, object]:
        return {
            "within_unit_duplicates": [
                {
                    "location": "Current.swift:PayrollLedger.grossWages",
                    "classification": "STRUCTURAL",
                    "is_exception": False,
                    "reasoning": "The method repeats the accumulation sequence.",
                    "evidence": "The method filters, maps, and reduces payroll values.",
                },
                {
                    "location": "Current.swift:PayrollLedger.reimbursements",
                    "classification": "STRUCTURAL",
                    "is_exception": False,
                    "reasoning": "The method repeats the accumulation sequence.",
                    "evidence": "The method filters, maps, and reduces payroll values.",
                },
            ],
            "missing_abstractions": [
                {
                    "location": "Current.swift:PayrollLedger",
                    "pattern": "payroll accumulation",
                    "is_exception": False,
                    "reasoning": "The reusable accumulation pipeline remains inline.",
                    "evidence": "Two methods implement the same generic pipeline.",
                }
            ],
        }

    @staticmethod
    def _empty_target_analysis_output() -> dict[str, object]:
        return {
            "within_unit_duplicates": [],
            "missing_abstractions": [],
        }

    @staticmethod
    def _exception_output(
        is_exception: bool = False,
    ) -> dict[str, object]:
        return {
            "is_exception": is_exception,
            "additional_info": {
                "reasoning": "Classified the whole unit after both DRY analysis lanes.",
                "evidence": "Current.swift and the selected repository candidate.",
            },
        }

    def _result(self, run_id: str) -> RuleReviewResult:
        return RuleReviewResult.model_validate_json(
            (
                self.project_root
                / ".solid-coder"
                / "runs"
                / run_id
                / "results"
                / "review"
                / "dry"
                / run_id
                / "result.json"
            ).read_text()
        )

    def _assert_operation_events(self, run_id: str) -> None:
        events = [
            json.loads(line)
            for line in (
                self.run_root / run_id / "events.jsonl"
            ).read_text().splitlines()
        ]
        completions = {
            event["step_id"]: event
            for event in events
            if event["event"] == "step_completed"
            and event["step_id"].endswith(
                ("search_repository", "validate_selection")
            )
        }
        self.assertEqual(len(completions), 2)
        self.assertTrue(
            all(event["session_id"] == "engine" for event in completions.values())
        )
        search_completion = next(
            event
            for step_id, event in completions.items()
            if step_id.endswith("search_repository")
        )
        candidates = search_completion["outputs"]["candidates"]
        self.assertEqual(
            [candidate["source_identity"] for candidate in candidates],
            ["SharedTaxFormatter.swift"],
        )


if __name__ == "__main__":
    unittest.main()
