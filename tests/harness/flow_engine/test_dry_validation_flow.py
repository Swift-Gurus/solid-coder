"""Tests the file-scoped DRY workflow and MCP-owned repository comparison."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from harness.flow_run_orchestrator_factory import FlowRunOrchestratorFactory
from harness.rule_review_result import RuleReviewResult
from harness.runs_base_dir_resolver import RunsBaseDirResolver
from harness.static_session_id_reader import StaticSessionIdReader
from rule_instruction_block_reader import RuleInstructionBlockReader
from source.source_operation_registrations_factory import (
    SourceOperationRegistrationsFactory,
)


_PROJECT_ROOT = Path(__file__).resolve().parents[3]


"""
solid-name: TestDryValidationFlow
solid-category: integration-test
solid-spec: [SPEC-039, SPEC-040]
solid-description: Proves DRY local analysis, typed repository comparison, canonical metrics, audit events, and MCP scoring.
"""
class TestDryValidationFlow(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project_root = Path(temporary.name)
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
            operation_registrations=SourceOperationRegistrationsFactory().make(),
        ).build()

    def test_executes_local_and_external_lanes_before_mcp_scoring(self) -> None:
        started = self.engine.flow_start("dry", self._parameters())

        self.assertIsNone(started.error, started.error)
        self.assertEqual(
            {step.step_id for step in started.steps},
            {"internal_duplications", "target_search-1.generate_terms"},
        )
        classified = self.engine.flow_next({
            step.instance_id: self._initial_output(
                step.step_id,
                "SharedTaxFormatter",
            )
            for step in started.steps
        })

        self.assertEqual(len(classified.steps), 1)
        candidate_prompt = classified.steps[0].prompt
        self.assertIn("struct SharedTaxFormatter", candidate_prompt)
        self.assertIn("struct PayrollLedger", candidate_prompt)
        self.assertEqual(
            candidate_prompt.count("Return only one JSON object matching this schema"),
            1,
        )
        measured = self.engine.flow_next({
            classified.steps[0].instance_id: self._candidate_assessment()
        })

        self.assertEqual(
            {step.step_id for step in measured.steps},
            {"reuse_misses", "duplicate_sites", "missing_abstractions", "classify_exception"},
        )
        completed = self.engine.flow_next({
            step.instance_id: self._measurement_output(step.step_id)
            for step in measured.steps
        })

        self.assertEqual(completed.status, "done")
        result = self._result(started.run_id)
        self.assertEqual(result.workflow_id, "dry")
        self.assertEqual(
            [metric.metric_id for metric in result.metrics],
            ["DRY-1", "DRY-2", "DRY-3"],
        )
        self.assertEqual([metric.value for metric in result.metrics], [1, 2, 1])
        self.assertEqual(result.severity, "SEVERE")
        self.assertEqual(result.scoring_authority, "mcp")
        self._assert_operation_events(started.run_id)

    def test_embeds_canonical_detection_and_exception_instructions(self) -> None:
        started = self.engine.flow_start("dry", self._parameters())
        classified = self.engine.flow_next({
            step.instance_id: self._initial_output(
                step.step_id,
                "SharedTaxFormatter",
            )
            for step in started.steps
        })
        measured = self.engine.flow_next({
            classified.steps[0].instance_id: self._candidate_assessment()
        })
        prompts = {step.step_id: step.prompt for step in measured.steps}
        rule = (_PROJECT_ROOT / "references/principles/DRY/rule.md").read_text()
        reader = RuleInstructionBlockReader()

        self.assertIn(
            reader.detection(rule, "DRY-1", "Reuse Miss"),
            prompts["reuse_misses"],
        )
        self.assertIn(
            reader.detection(rule, "DRY-2", "Inlined Duplication"),
            prompts["duplicate_sites"],
        )
        self.assertIn(
            reader.detection(rule, "DRY-3", "Missing Abstraction"),
            prompts["missing_abstractions"],
        )
        self.assertIn(reader.exceptions(rule), prompts["classify_exception"])

    def test_keeps_local_duplication_lane_when_repository_search_is_empty(self) -> None:
        (self.project_root / "SharedTaxFormatter.swift").unlink()
        started = self.engine.flow_start("dry", self._parameters())
        measured = self.engine.flow_next({
            step.instance_id: self._initial_output(
                step.step_id,
                "NoRepositoryCandidate",
            )
            for step in started.steps
        })

        self.assertIsNone(measured.error, measured.error)
        duplicate_prompt = next(
            step.prompt
            for step in measured.steps
            if step.step_id == "duplicate_sites"
        )
        self.assertIn("first and second contain the same sequence", duplicate_prompt)

    def _parameters(self) -> dict[str, object]:
        return {
            "project_root": str(self.project_root),
            "search_granularity": "unit",
            "review_source": {
                "kind": "text",
                "text": self.current_content,
                "virtual_path": str(self.current_path.resolve()),
            },
        }

    @staticmethod
    def _initial_output(
        step_id: str,
        generated_term: str,
    ) -> dict[str, object]:
        if step_id == "internal_duplications":
            return {
                "local_duplicate_sites": [
                    {
                        "classification": "IDENTICAL",
                        "evidence": "first and second contain the same sequence",
                        "locations": ["line 2", "line 3"],
                    }
                ]
            }
        return {"generated_terms": [generated_term]}

    @staticmethod
    def _candidate_assessment() -> dict[str, object]:
        return {
            "assessment": {
                "classification": "EXACT",
                "reasoning": "The candidate covers the same formatting responsibility.",
                "evidence": "Both units implement the same formatter behavior.",
            }
        }

    @staticmethod
    def _measurement_output(step_id: str) -> dict[str, object]:
        additional_info = {
            "reasoning": f"Measured {step_id} from both DRY analysis lanes.",
            "evidence": "Current.swift lines 2-3 and SharedTaxFormatter.swift",
        }
        if step_id == "classify_exception":
            return {
                "is_exception": False,
                "additional_info": additional_info,
            }
        values = {
            "reuse_misses": 1,
            "duplicate_sites": 2,
            "missing_abstractions": 1,
        }
        return {"value": values[step_id], "additional_info": additional_info}

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
                ("search_repository", "read_candidates")
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
