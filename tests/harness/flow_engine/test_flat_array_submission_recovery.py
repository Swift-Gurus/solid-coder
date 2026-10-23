"""Exercises flat addressing through the real flow lifecycle."""

import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from harness.flow_result_json_renderer import FlowResultJsonRenderer
from harness.flow_run_orchestrator_factory import FlowRunOrchestratorFactory
from harness.flow_submission_format import FlowSubmissionFormat
from harness.runs_base_dir_resolver import RunsBaseDirResolver
from pipeline.flow_result_renderer_creator import FlowResultRendererCreator

"""
solid-name: TestFlatArraySubmissionRecovery
solid-category: unit-test
solid-spec: [SPEC-068]
solid-description: Exercises flat submission completion, invalid envelopes, partial recovery, and stable replay addresses through the engine.
"""


class TestFlatArraySubmissionRecovery(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.workflow = self.root / "workflow.yaml"
        self.workflow.write_text(
            textwrap.dedent("""
            id: flat-experiment
            name: Flat Experiment
            max_turns: 10
            execution: {mode: aggregate}
            presentation: {mode: combined}
            steps:
              - id: classify_actions
                prompt: Classify actions.
                outputs:
                  - name: actions
                    type: data
                    schema: {type: array, items: {type: string}}
              - id: classify_dependencies
                prompt: Classify dependencies.
                outputs:
                  - name: dependencies
                    type: data
                    schema: {type: array, items: {type: string}}
        """),
            encoding="utf-8",
        )
        self.factory = FlowRunOrchestratorFactory(
            base_dir_resolver=RunsBaseDirResolver(project_dir_fn=lambda: self.root),
            plugin_root=self.root,
            submission_format=FlowSubmissionFormat.FLAT_ARRAY,
        )
        self.engine = self.factory.build()

    def test_partial_results_keep_addresses_after_restart(self) -> None:
        started = self.engine.flow_start(str(self.workflow), isolated=True)
        self.assertIsNone(started.error)
        self.assertEqual(len(started.steps), 2)
        first, second = started.steps
        self.assertNotEqual(first.submission_id, second.submission_id)
        self.assertTrue(first.submission_id)
        remaining = self.engine.flow_next(
            outputs={
                "submissions": [
                    {"id": first.submission_id, "result": {"actions": ["load"]}},
                ]
            },
            run_id=started.run_id,
        )
        self.assertIsNone(remaining.error)
        self.assertEqual(
            [step.submission_id for step in remaining.steps], [second.submission_id]
        )
        restarted = self.factory.build()
        completed = restarted.flow_next(
            outputs={
                "submissions": [
                    {"id": second.submission_id, "result": {"dependencies": []}},
                ]
            },
            run_id=started.run_id,
        )
        self.assertIsNone(completed.error)
        self.assertEqual(completed.status, "done")

    def test_duplicate_ids_reject_before_any_completion(self) -> None:
        started = self.engine.flow_start(str(self.workflow), isolated=True)
        first = started.steps[0]
        rejected = self.engine.flow_next(
            outputs={
                "submissions": [
                    {"id": first.submission_id, "result": {"actions": []}},
                    {"id": first.submission_id, "result": {"actions": []}},
                ]
            },
            run_id=started.run_id,
        )
        self.assertIn("duplicate", rejected.error.lower())
        completed = self.engine.flow_next(
            outputs={
                "submissions": [
                    {
                        "id": started.steps[1].submission_id,
                        "result": {"dependencies": []},
                    },
                    {"id": first.submission_id, "result": {"actions": []}},
                ]
            },
            run_id=started.run_id,
        )
        self.assertIsNone(completed.error)
        self.assertEqual(completed.status, "done")

    def test_production_renderer_explains_flat_results(self) -> None:
        started = self.engine.flow_start(str(self.workflow), isolated=True)
        rendered = FlowResultRendererCreator().create().render_start(started)
        self.assertIn('"submissions"', rendered)
        self.assertIn('"result"', rendered)
        self.assertIn(started.steps[0].submission_id, rendered)
        self.assertIn(started.steps[1].submission_id, rendered)
        self.assertIn("Classify actions.", rendered)
        self.assertNotIn("keyed", rendered)

    def test_invalid_result_retains_valid_sibling_and_corrects_only_failed_id(
        self,
    ) -> None:
        started = self.engine.flow_start(str(self.workflow), isolated=True)
        first, second = started.steps
        remaining = self.engine.flow_next(
            outputs={
                "submissions": [
                    {"id": first.submission_id, "result": {"actions": "wrong"}},
                    {"id": second.submission_id, "result": {"dependencies": []}},
                ]
            },
            run_id=started.run_id,
        )
        self.assertIsNone(remaining.error)
        self.assertEqual(
            [step.submission_id for step in remaining.steps], [first.submission_id]
        )
        rendered = FlowResultRendererCreator().create().render_next(remaining)
        self.assertIn("Rejected:", rendered)
        self.assertIn("array", rendered)
        self.assertIn("complete result", rendered)
        self.assertIn("Accepted assignments are already saved", rendered)
        completed = self.engine.flow_next(
            outputs={
                "submissions": [
                    {"id": first.submission_id, "result": {"actions": []}},
                ]
            },
            run_id=started.run_id,
        )
        self.assertEqual(completed.status, "done")

    def test_format_survives_configuration_change_on_restart(self) -> None:
        started = self.engine.flow_start(str(self.workflow), isolated=True)
        nested_engine = FlowRunOrchestratorFactory(
            base_dir_resolver=RunsBaseDirResolver(project_dir_fn=lambda: self.root),
            plugin_root=self.root,
        ).build()
        completed = nested_engine.flow_next(
            outputs={
                "submissions": [
                    {"id": started.steps[0].submission_id, "result": {"actions": []}},
                    {
                        "id": started.steps[1].submission_id,
                        "result": {"dependencies": []},
                    },
                ]
            },
            run_id=started.run_id,
        )
        self.assertEqual(completed.status, "done")

    def test_unknown_id_and_malformed_envelope_do_not_accept_valid_sibling(
        self,
    ) -> None:
        for invalid in [
            {"submissions": [{"id": "unknown", "result": {}}]},
            {"submissions": [{"id": "a1", "result": []}]},
            {"submissions": "not an array"},
            {"submissions": [], "extra": True},
        ]:
            with self.subTest(invalid=invalid):
                started = self.engine.flow_start(str(self.workflow), isolated=True)
                rejected = self.engine.flow_next(outputs=invalid, run_id=started.run_id)
                self.assertTrue(rejected.error)
                completed = self.engine.flow_next(
                    outputs={
                        "submissions": [
                            {
                                "id": started.steps[0].submission_id,
                                "result": {"actions": []},
                            },
                            {
                                "id": started.steps[1].submission_id,
                                "result": {"dependencies": []},
                            },
                        ]
                    },
                    run_id=started.run_id,
                )
                self.assertEqual(completed.status, "done")

    def test_json_response_retains_flat_submission_instructions(self) -> None:
        started = self.engine.flow_start(str(self.workflow), isolated=True)
        renderer = FlowResultJsonRenderer(
            flat_renderer=FlowResultRendererCreator().create()
        )
        rendered = json.loads(renderer.render_start(started))
        self.assertEqual(rendered["run_id"], started.run_id)
        self.assertIn('"submissions"', rendered["instructions"])
        self.assertIn(started.steps[0].submission_id, rendered["instructions"])

    def test_existing_aggregate_fixture_scores_and_resumes_after_engine_boundary(
        self,
    ) -> None:
        fixture = (
            Path(__file__).parent
            / "fixtures/aggregate_co_located_metrics/workflow.yaml"
        )
        started = self.engine.flow_start(str(fixture), isolated=True)
        self.assertEqual(len(started.steps), 3)
        classified = [
            {
                "actions": [
                    {"name": "initialize", "is_lifecycle": True},
                    {"name": "load", "is_lifecycle": False},
                    {"name": "save", "is_lifecycle": False},
                ]
            },
            {
                "method_variable_usage": [
                    {"method": "load", "variables": ["cache"]},
                    {"method": "save", "variables": ["cache", "storage"]},
                    {"method": "render", "variables": ["view"]},
                ]
            },
            {"stakeholders": ["Operations", "Presentation"]},
        ]
        remaining = self.engine.flow_next(
            outputs={
                "submissions": [
                    {"id": step.submission_id, "result": classified[index]}
                    for index, step in reversed(list(enumerate(started.steps)))
                ]
            },
            run_id=started.run_id,
        )
        self.assertIsNone(remaining.error)
        self.assertEqual(
            [step.step_id for step in remaining.steps], ["classify_exception"]
        )
        self.assertIn("actions=2", remaining.steps[0].prompt)
        self.assertIn("groups=2", remaining.steps[0].prompt)
        self.assertIn("stakeholders=2", remaining.steps[0].prompt)
        replayed = self.factory.build().flow_next(run_id=started.run_id)
        self.assertIsNone(replayed.error)
        self.assertEqual(
            replayed.steps[0].submission_id, remaining.steps[0].submission_id
        )
        completed = self.engine.flow_next(
            outputs={
                "submissions": [
                    {
                        "id": replayed.steps[0].submission_id,
                        "result": {
                            "is_exception": False,
                            "additional_info": {
                                "reasoning": "No rule exception applies.",
                                "evidence": "All three engine metrics are two.",
                            },
                        },
                    }
                ]
            },
            run_id=started.run_id,
        )
        self.assertEqual(completed.status, "done")
        result_path = (
            self.root
            / "runs/subagents"
            / started.run_id
            / "results/review/aggregate-classifiers"
            / started.run_id
            / "result.json"
        )
        result = json.loads(result_path.read_text())
        self.assertEqual([metric["value"] for metric in result["metrics"]], [2, 2, 2])
        self.assertEqual(
            [metric["severity"] for metric in result["metrics"]], ["SEVERE"] * 3
        )

    def test_unpresented_ready_step_cannot_be_submitted_and_accepted_id_becomes_stale(
        self,
    ) -> None:
        self.workflow.write_text(
            self.workflow.read_text()
            .replace(
                "execution: {mode: aggregate}",
                "execution: {mode: granular}",
            )
            .replace(
                "presentation: {mode: combined}", "presentation: {mode: individual}"
            )
        )
        started = self.engine.flow_start(str(self.workflow), isolated=True)
        first, second = started.steps
        rendered = FlowResultRendererCreator().create().render_start(started)
        self.assertNotIn(f"{second.submission_id}: target", rendered)
        rejected = self.engine.flow_next(
            outputs={
                "submissions": [
                    {"id": second.submission_id, "result": {"dependencies": []}},
                ]
            },
            run_id=started.run_id,
        )
        self.assertIn("unpresented", rejected.error)
        remaining = self.engine.flow_next(
            outputs={
                "submissions": [
                    {"id": first.submission_id, "result": {"actions": []}},
                ]
            },
            run_id=started.run_id,
        )
        self.assertEqual(remaining.steps[0].submission_id, second.submission_id)
        stale = self.engine.flow_next(
            outputs={
                "submissions": [
                    {"id": first.submission_id, "result": {"actions": []}},
                ]
            },
            run_id=started.run_id,
        )
        self.assertIn("stale", stale.error)
