"""Proves aggregate execution completes original workflow steps."""

from __future__ import annotations

import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from harness.flow_run_orchestrator_factory import FlowRunOrchestratorFactory
from harness.batch_step_renderer_factory import BatchStepRendererFactory
from harness.first_ready_step_selector import FirstReadyStepSelector
from harness.flow_result_renderer import FlowResultRenderer
from harness.runs_base_dir_resolver import RunsBaseDirResolver
from harness.sibling_batch_step_selector_factory import SiblingBatchStepSelectorFactory
from harness.single_step_renderer import SingleStepRenderer
from harness.step_formatter import StepFormatter
from harness.step_renderer import StepRenderer
from harness.subagent_delegator import SubagentDelegator
from harness.terminal_message_resolver import TerminalMessageResolver


"""
solid-name: TestAggregateWorkflowExecution
solid-category: integration-test
solid-spec: [SPEC-045]
solid-description: Proves one aggregate model turn validates and records each original dependent workflow step.
"""
class TestAggregateWorkflowExecution(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project_root = Path(temporary.name)
        self.workflow = self.project_root / "aggregate.yaml"
        self.workflow.write_text(
            textwrap.dedent(
                """
                id: aggregate-flow
                name: Aggregate Flow
                execution:
                  mode: aggregate
                steps:
                  - id: inspect
                    prompt: Inspect the target.
                    outputs:
                      - name: analysis
                        type: data
                        schema: {type: string}
                  - id: decide
                    prompt: Decide whether it passes.
                    depends_on: [inspect]
                    outputs:
                      - name: result
                        type: data
                        schema: {type: boolean}
                """
            ),
            encoding="utf-8",
        )
        self.sut = FlowRunOrchestratorFactory(
            base_dir_resolver=RunsBaseDirResolver(
                project_dir_fn=lambda: self.project_root
            ),
            plugin_root=self.project_root,
        ).build()
        self.renderer = FlowResultRenderer(
            step_renderer=StepRenderer(
                ready_step_selector=FirstReadyStepSelector(),
                sibling_batch_selector=SiblingBatchStepSelectorFactory().make(),
                single_step_renderer=SingleStepRenderer(
                    subagent_delegator=SubagentDelegator(),
                    step_formatter=StepFormatter(),
                ),
                batch_step_renderer=BatchStepRendererFactory().make(),
            ),
            terminal_message_resolver=TerminalMessageResolver(),
        )

    def test_one_submission_completes_both_original_steps(self) -> None:
        started = self.sut.flow_start(str(self.workflow))

        self.assertIsNone(started.error)
        self.assertEqual(len(started.steps), 2)
        rendered = self.renderer.render_start(started)
        self.assertEqual(rendered.count("Inspect the target."), 1)
        self.assertEqual(rendered.count("Decide whether it passes."), 1)
        self.assertNotIn(
            "Return only one JSON object matching this schema.",
            rendered,
        )
        self.assertEqual(
            rendered.count("Call flow_next with one JSON object matching this schema."),
            1,
        )

        completed = self.sut.flow_next({
            "aggregate-flow": {
                "aggregate-flow": {
                    "inspect": {"analysis": "The target was inspected."},
                    "decide": {"result": True},
                }
            }
        })

        self.assertEqual(completed.status, "done", completed.error)
        events = [
            json.loads(line)
            for line in (
                self.project_root
                / "runs"
                / started.run_id
                / "events.jsonl"
            ).read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual(
            [event["step_id"] for event in events if event["event"] == "step_completed"],
            ["inspect", "decide"],
        )

    def test_partial_submission_completes_once_and_returns_only_missing_step(self) -> None:
        started = self.sut.flow_start(str(self.workflow))

        remaining = self.sut.flow_next({
            "aggregate-flow": {
                "aggregate-flow": {
                    "inspect": {"analysis": "The target was inspected."},
                }
            }
        })

        self.assertEqual(remaining.status, "ready", remaining.error)
        self.assertEqual([step.step_id for step in remaining.steps], ["decide"])
        completed = [
            event["step_id"]
            for event in self._events(started.run_id)
            if event["event"] == "step_completed"
        ]
        self.assertEqual(completed, ["inspect"])

        finished = self.sut.flow_next({
            "aggregate-flow": {
                "aggregate-flow": {
                    "decide": {"result": True},
                }
            }
        })

        self.assertEqual(finished.status, "done", finished.error)
        completed = [
            event["step_id"]
            for event in self._events(started.run_id)
            if event["event"] == "step_completed"
        ]
        self.assertEqual(completed, ["inspect", "decide"])

    def test_invalid_sibling_retries_without_reopening_valid_step(self) -> None:
        started = self.sut.flow_start(str(self.workflow))

        remaining = self.sut.flow_next({
            "aggregate-flow": {
                "aggregate-flow": {
                    "inspect": {"analysis": "The target was inspected."},
                    "decide": {"result": "not-a-boolean"},
                }
            }
        })

        self.assertEqual([step.step_id for step in remaining.steps], ["decide"])
        self.assertIn("not of type 'boolean'", remaining.steps[0].rejection_reason)
        completed = [
            event["step_id"]
            for event in self._events(started.run_id)
            if event["event"] == "step_completed"
        ]
        self.assertEqual(completed, ["inspect"])

    def test_unknown_address_is_rejected_without_completing_work(self) -> None:
        started = self.sut.flow_start(str(self.workflow))

        rejected = self.sut.flow_next({
            "aggregate-flow": {
                "aggregate-flow": {
                    "invented": {},
                }
            }
        })

        self.assertIn("Unknown aggregate address", rejected.error)
        self.assertFalse(any(
            event["event"] == "step_completed"
            for event in self._events(started.run_id)
        ))

    def test_replay_returns_only_the_incomplete_original_step(self) -> None:
        started = self.sut.flow_start(str(self.workflow))
        self.sut.flow_next({
            "aggregate-flow": {
                "aggregate-flow": {
                    "inspect": {"analysis": "The target was inspected."},
                }
            }
        })
        restarted = FlowRunOrchestratorFactory(
            base_dir_resolver=RunsBaseDirResolver(
                project_dir_fn=lambda: self.project_root
            ),
            plugin_root=self.project_root,
        ).build()

        replayed = restarted.flow_next({})

        self.assertEqual([step.step_id for step in replayed.steps], ["decide"])

    def test_combines_aggregate_child_workflow_across_for_each_items(self) -> None:
        child_directory = self.project_root / "workflows" / "alpha"
        child_directory.mkdir(parents=True)
        (child_directory / "workflow.yaml").write_text(
            textwrap.dedent(
                """
                id: alpha
                name: Alpha
                max_turns: 5
                steps:
                  - id: inspect
                    prompt: Inspect each assigned item.
                    outputs:
                      - name: analysis
                        type: data
                        schema: {type: string}
                  - id: decide
                    prompt: Decide for each assigned item.
                    depends_on: [inspect]
                    outputs:
                      - name: result
                        type: data
                        schema: {type: boolean}
                """
            ),
            encoding="utf-8",
        )
        combined = self.project_root / "combined.yaml"
        combined.write_text(
            textwrap.dedent(
                """
                id: combined
                name: Combined
                steps:
                  - id: prepare
                    prompt: Prepare items.
                    outputs:
                      - name: items
                        type: data
                        schema:
                          type: array
                          items:
                            type: object
                            additionalProperties: false
                            required: [name, enabled]
                            properties:
                              name: {type: string}
                              enabled: {type: boolean}
                  - group: selected_work
                    execution:
                      mode: aggregate
                    presentation:
                      mode: combined
                    steps:
                      - include:
                          workflow: alpha
                        as: alpha
                        depends_on: [prepare]
                        for_each:
                          source: "{{steps.prepare.outputs.items}}"
                          mode: batch
                          label: "{{item.name}}"
                        when:
                          ref: "{{item.enabled}}"
                          equals: true
                """
            ),
            encoding="utf-8",
        )
        started = self.sut.flow_start(str(combined))

        ready = self.sut.flow_next({
            started.steps[0].instance_id: {
                "items": [
                    {"name": "A", "enabled": True},
                    {"name": "Skipped", "enabled": False},
                    {"name": "B", "enabled": True},
                ]
            }
        })

        self.assertEqual(len(ready.steps), 4)
        rendered = self.renderer.render_next(ready)
        self.assertEqual(rendered.count("Inspect each assigned item."), 1)
        self.assertEqual(rendered.count("Decide for each assigned item."), 1)
        self.assertIn("A: alpha", rendered)
        self.assertIn("B: alpha", rendered)
        self.assertNotIn("Skipped", rendered)

        completed = self.sut.flow_next({
            "A": {
                "alpha": {
                    "inspect": {"analysis": "A inspected"},
                    "decide": {"result": True},
                }
            },
            "B": {
                "alpha": {
                    "inspect": {"analysis": "B inspected"},
                    "decide": {"result": False},
                }
            },
        })

        self.assertEqual(completed.status, "done", completed.error)
        self.assertEqual(
            [
                event["step_id"]
                for event in self._events(started.run_id)
                if event["event"] == "step_skipped"
            ],
            [
                "selected_work.alpha-2.inspect",
                "selected_work.alpha-2.decide",
            ],
        )

    def test_aggregates_every_root_for_each_instance_without_crossing_fan_out(self) -> None:
        workflow = self.project_root / "root-batch.yaml"
        workflow.write_text(
            textwrap.dedent(
                """
                id: root-batch
                name: Root Batch
                max_turns: 5
                execution:
                  mode: aggregate
                steps:
                  - id: prepare
                    prompt: Prepare items.
                    outputs:
                      - name: items
                        type: data
                        schema:
                          type: array
                          items: {type: string}
                  - id: review
                    prompt: Review every assigned item.
                    depends_on: [prepare]
                    for_each:
                      source: "{{steps.prepare.outputs.items}}"
                      mode: batch
                      label: "{{item}}"
                    outputs:
                      - name: result
                        type: data
                        schema: {type: string}
                """
            ),
            encoding="utf-8",
        )
        started = self.sut.flow_start(str(workflow))

        ready = self.sut.flow_next({
            "root-batch": {
                "root-batch": {
                    "prepare": {"items": ["A", "B"]},
                }
            }
        })

        self.assertEqual([step.instance_id for step in ready.steps], ["review-1", "review-2"])
        rendered = self.renderer.render_next(ready)
        self.assertEqual(rendered.count("Review every assigned item."), 1)
        self.assertIn("A: root-batch", rendered)
        self.assertIn("B: root-batch", rendered)

        completed = self.sut.flow_next({
            "A": {"root-batch": {"review": {"result": "A reviewed"}}},
            "B": {"root-batch": {"review": {"result": "B reviewed"}}},
        })

        self.assertEqual(completed.status, "done", completed.error)

    def _events(self, run_id: str) -> list[dict[str, object]]:
        return [
            json.loads(line)
            for line in (
                self.project_root / "runs" / run_id / "events.jsonl"
            ).read_text(encoding="utf-8").splitlines()
        ]


if __name__ == "__main__":
    unittest.main()
