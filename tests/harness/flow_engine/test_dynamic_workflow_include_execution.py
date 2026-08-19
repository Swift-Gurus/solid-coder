"""Validates per-item execution of dynamically included workflow DAGs."""

from __future__ import annotations

import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from harness.flow_run_orchestrator import FlowRunOrchestrator
from harness.flow_run_orchestrator_factory import FlowRunOrchestratorFactory
from harness.runs_base_dir_resolver import RunsBaseDirResolver


class TestDynamicWorkflowIncludeExecution(unittest.TestCase):

    def setUp(self) -> None:
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self.project_root = Path(temporary_directory.name)
        self.flow_path = self._write_workflows()
        self.sut = FlowRunOrchestratorFactory(
            base_dir_resolver=RunsBaseDirResolver(
                project_dir_fn=lambda: self.project_root
            ),
            plugin_root=self.project_root,
        ).build()

    def test_waits_then_expands_one_child_workflow_root_per_source_item(self) -> None:
        initial = self._start()

        self.assertEqual([step.step_id for step in initial.steps], ["prepare"])

        expanded = self.sut.flow_next(
            {
                initial.steps[0].instance_id: {
                    "units": [{"name": "Alpha"}, {"name": "Beta"}],
                }
            }
        )
        self.assertIsNone(expanded.error, expanded.error)

        self.assertEqual(
            [step.step_id for step in expanded.steps],
            ["review-1.inspect", "review-2.inspect"],
        )
        self.assertEqual(
            [step.prompt.splitlines()[0] for step in expanded.steps],
            ["Inspect Alpha.", "Inspect Beta."],
        )

    def test_engine_owned_prepare_releases_dynamic_roots_during_start(self) -> None:
        flow_path = self.project_root / "engine-prepared-parent.yaml"
        flow_path.write_text(
            textwrap.dedent(
                """
                name: engine_prepared_parent
                max_turns: 20
                steps:
                  - id: prepare
                    type: command
                    command: >
                      python3 -c "import json; print(json.dumps({'units': [{'name': 'Alpha'}, {'name': 'Beta'}]}))"
                    outputs:
                      - name: units
                        type: data
                        schema:
                          type: array
                          items:
                            type: object
                            properties:
                              name: {type: string}
                            required: [name]
                  - include: child.yaml
                    as: review
                    depends_on: [prepare]
                    for_each: "{{steps.prepare.outputs.units}}"
                    with:
                      review_unit: "{{item}}"
                  - id: summarize
                    depends_on: [review]
                    prompt: Summarize completed reviews.
                """
            ),
            encoding="utf-8",
        )

        result = self.sut.flow_start(str(flow_path))

        self.assertIsNone(result.error, result.error)
        self.assertEqual(
            [step.step_id for step in result.steps],
            ["review-1.inspect", "review-2.inspect"],
        )
        reports = self.sut.flow_next({
            result.steps[0].instance_id: {"finding": "Alpha finding"},
            result.steps[1].instance_id: {"finding": "Beta finding"},
        })
        self.assertEqual(
            [step.step_id for step in reports.steps],
            ["review-1.report", "review-2.report"],
        )
        self.assertEqual(
            [step.prompt.splitlines()[0] for step in reports.steps],
            [
                "Report Alpha using Alpha finding.",
                "Report Beta using Beta finding.",
            ],
        )
        summarized = self.sut.flow_next({
            reports.steps[0].instance_id: {"report": "Alpha report"},
            reports.steps[1].instance_id: {"report": "Beta report"},
        })
        self.assertEqual(
            [step.step_id for step in summarized.steps],
            ["summarize"],
        )

    def test_completed_root_releases_only_its_own_child_dag(self) -> None:
        initial = self._start()
        expanded = self.sut.flow_next(
            {
                initial.steps[0].instance_id: {
                    "units": [{"name": "Alpha"}, {"name": "Beta"}],
                }
            }
        )
        self.assertIsNone(expanded.error, expanded.error)

        result = self.sut.flow_next(
            {
                expanded.steps[0].instance_id: {
                    "finding": "Alpha finding",
                }
            }
        )

        self.assertIsNone(result.error, result.error)
        self.assertEqual(
            {step.step_id for step in result.steps},
            {"review-1.report", "review-2.inspect"},
        )
        prompts_by_step = {step.step_id: step.prompt for step in result.steps}
        self.assertEqual(
            prompts_by_step["review-1.report"].splitlines()[0],
            "Report Alpha using Alpha finding.",
        )
        self.assertEqual(
            prompts_by_step["review-2.inspect"].splitlines()[0],
            "Inspect Beta.",
        )

    def test_include_condition_skips_inapplicable_child_instances(self) -> None:
        conditional_path = self.project_root / "conditional-parent.yaml"
        conditional_path.write_text(
            textwrap.dedent(
                """
                name: conditional_parent
                max_turns: 20
                steps:
                  - id: prepare
                    prompt: Prepare units.
                    outputs:
                      - name: units
                        type: data
                        schema:
                          type: array
                          items: {type: object}
                  - include: child.yaml
                    as: review
                    depends_on: [prepare]
                    for_each: "{{steps.prepare.outputs.units}}"
                    with:
                      review_unit: "{{item}}"
                    when:
                      ref: "{{item.file_extension}}"
                      equals: .swift
                """
            ),
            encoding="utf-8",
        )
        initial = self.sut.flow_start(str(conditional_path))

        result = self.sut.flow_next(
            {
                initial.steps[0].instance_id: {
                    "units": [
                        {"name": "Dashboard", "file_extension": ".swift"},
                        {"name": "Readme", "file_extension": ".md"},
                    ]
                }
            }
        )

        self.assertIsNone(result.error, result.error)
        self.assertEqual(
            [step.step_id for step in result.steps],
            ["review-1.inspect"],
        )
        skipped = [
            event
            for event in self._events(initial.run_id)
            if event.get("event") == "step_skipped"
        ]
        self.assertEqual(
            [event["step_id"] for event in skipped],
            ["review-2.inspect", "review-2.report"],
        )

    def test_completes_child_dags_and_records_their_source_associations(self) -> None:
        initial = self._start()
        roots = self.sut.flow_next(
            {
                initial.steps[0].instance_id: {
                    "units": [{"name": "Alpha"}, {"name": "Beta"}],
                }
            }
        )
        reports = self.sut.flow_next({
            step.instance_id: {
                "finding": f"{step.step_id} finding",
            }
            for step in roots.steps
        })
        completed = self.sut.flow_next({
            step.instance_id: {
                "report": f"{step.step_id} complete",
            }
            for step in reports.steps
        })

        self.assertEqual(
            completed.status,
            "done",
            (completed.error, [step.step_id for step in completed.steps]),
        )
        completed_events = {
            event["step_id"]: event
            for event in self._events(initial.run_id)
            if event.get("event") == "step_completed"
            and event.get("step_id", "").startswith("review-")
        }
        self.assertEqual(
            completed_events["review-1.inspect"]["item"],
            {"name": "Alpha"},
        )
        self.assertEqual(
            completed_events["review-1.report"]["item"],
            {"name": "Alpha"},
        )
        self.assertEqual(
            completed_events["review-2.inspect"]["item"],
            {"name": "Beta"},
        )
        self.assertEqual(
            completed_events["review-2.report"]["item"],
            {"name": "Beta"},
        )
        self.assertEqual(
            completed_events["review-1.inspect"]["workflow_source_index"],
            0,
        )
        self.assertEqual(
            completed_events["review-1.report"]["workflow_source_index"],
            0,
        )
        self.assertEqual(
            completed_events["review-2.inspect"]["workflow_source_index"],
            1,
        )
        self.assertEqual(
            completed_events["review-2.report"]["workflow_source_index"],
            1,
        )
        self.assertEqual(
            completed_events["review-1.inspect"]["workflow_instance_id"],
            "review-1",
        )
        self.assertEqual(
            completed_events["review-1.inspect"]["local_step_id"],
            "inspect",
        )
        self.assertEqual(
            completed_events["review-1.report"]["local_step_id"],
            "report",
        )
        self.assertEqual(
            completed_events["review-2.inspect"]["workflow_instance_id"],
            "review-2",
        )
        self.assertEqual(
            completed_events["review-2.inspect"]["local_step_id"],
            "inspect",
        )
        self.assertEqual(
            completed_events["review-2.report"]["local_step_id"],
            "report",
        )

    def _start(self):
        result = self.sut.flow_start(str(self.flow_path))
        self.assertIsNone(result.error, result.error)
        return result

    def _events(self, run_id: str) -> list[dict]:
        events_path = self.project_root / "runs" / run_id / "events.jsonl"
        return [
            json.loads(line)
            for line in events_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def _write_workflows(self) -> Path:
        (self.project_root / "child.yaml").write_text(
            textwrap.dedent(
                """
                id: child-review
                name: child_review
                inputs:
                  - name: review_unit
                    schema:
                      type: object
                      properties:
                        name: {type: string}
                      required: [name]
                steps:
                  - id: inspect
                    prompt: Inspect {{params.review_unit.name}}.
                    outputs:
                      - name: finding
                        type: data
                        schema: {type: string}
                  - id: report
                    prompt: >
                      Report {{params.review_unit.name}} using
                      {{steps.inspect.outputs.finding}}.
                    depends_on: [inspect]
                    outputs:
                      - name: report
                        type: data
                        schema: {type: string}
                """
            ),
            encoding="utf-8",
        )
        path = self.project_root / "parent.yaml"
        path.write_text(
            textwrap.dedent(
                """
                name: parent
                max_turns: 20
                steps:
                  - id: prepare
                    prompt: Prepare units.
                    outputs:
                      - name: units
                        type: data
                        schema:
                          type: array
                          items:
                            type: object
                            properties:
                              name: {type: string}
                            required: [name]
                  - include: child.yaml
                    as: review
                    depends_on: [prepare]
                    for_each: "{{steps.prepare.outputs.units}}"
                    with:
                      review_unit: "{{item}}"
                """
            ),
            encoding="utf-8",
        )
        return path


if __name__ == "__main__":
    unittest.main()
