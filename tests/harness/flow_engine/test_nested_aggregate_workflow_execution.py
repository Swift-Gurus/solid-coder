"""Exercises nested aggregate submissions through the real flow engine."""

import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from harness.aggregate_batch_step_presentation import AggregateBatchStepPresentation
from harness.combined_rule_batch_step_presentation import CombinedRuleBatchStepPresentation
from harness.flow_run_orchestrator_factory import FlowRunOrchestratorFactory
from harness.runs_base_dir_resolver import RunsBaseDirResolver
from harness.sibling_batch_step_selector_factory import SiblingBatchStepSelectorFactory


"""
solid-name: TestNestedAggregateWorkflowExecution
solid-category: unit-test
solid-spec: [SPEC-067]
solid-description: Proves nested candidate phases preserve every original result and scoped identity while combining compatible submissions.
"""
class TestNestedAggregateWorkflowExecution(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.sut = FlowRunOrchestratorFactory(
            base_dir_resolver=RunsBaseDirResolver(project_dir_fn=lambda: self.root),
            plugin_root=self.root,
        ).build()
        self._write("candidate", """
            id: candidate
            name: Candidate
            max_turns: 20
            outputs:
              - name: result
                type: data
                value: "{{steps.classify.outputs.result}}"
                schema: {type: string}
            steps:
              - id: inspect
                prompt: Inspect candidate {{params.candidate.name}} for {{params.target}}.
                outputs:
                  - name: evidence
                    type: data
                    schema: {type: string, minLength: 1}
              - id: classify
                depends_on: [inspect]
                prompt: Classify the inspected candidate.
                outputs:
                  - name: result
                    type: data
                    schema: {type: string, minLength: 1}
        """)
        self._write("target", """
            id: target
            name: Target
            max_turns: 20
            steps:
              - id: discover
                prompt: Identify candidates for {{params.target}}.
                outputs:
                  - name: candidates
                    type: data
                    schema:
                      type: array
                      items:
                        type: object
                        required: [name]
                        properties:
                          name: {type: string}
              - include: {workflow: candidate}
                as: candidates
                depends_on: [discover]
                for_each: "{{steps.discover.outputs.candidates}}"
                with:
                  target: "{{params.target}}"
                  candidate: "{{item}}"
        """)
        self.workflow = self._write("main", """
            id: main
            name: Main
            max_turns: 20
            steps:
              - id: prepare
                prompt: Prepare targets.
                outputs:
                  - name: targets
                    type: data
                    schema: {type: array, items: {type: string}}
              - group: combined
                execution: {mode: aggregate}
                presentation: {mode: combined}
                steps:
                  - include: {workflow: target}
                    as: targets
                    depends_on: [prepare]
                    for_each:
                      source: "{{steps.prepare.outputs.targets}}"
                      mode: batch
                      label: "{{item}}"
                    with:
                      target: "{{item}}"
        """)

    def test_one_nested_submission_completes_all_five_pairs(self) -> None:
        candidates = self._start_candidates()

        self.assertIsNone(candidates.error, candidates.error)
        self.assertEqual(len(candidates.steps), 10)
        self.assertTrue(all(isinstance(step.batch, AggregateBatchStepPresentation) for step in candidates.steps))
        self.assertEqual(len({step.batch.group for step in candidates.steps}), 1)
        self.assertEqual(len({step.instance_id for step in candidates.steps}), 10)
        finished = self.sut.flow_next(self._candidate_submission(candidates.steps))

        self.assertEqual(finished.status, "done", finished.error)
        events = [json.loads(line) for line in (self.root / "runs" / self.run_id / "events.jsonl").read_text().splitlines()]
        completions = [event for event in events if event["event"] == "step_completed"
                       and event["instance_id"] in {step.instance_id for step in candidates.steps}]
        self.assertEqual(len(completions), 10)
        for event in completions:
            self.assertEqual(list(event["outputs"].values()), [event["instance_id"]])
        self.assertEqual(sum(event["event"] == "turn_counted" for event in events), 3)

    def test_partial_invalid_nested_submission_replays_only_unfinished_work(self) -> None:
        candidates = self._start_candidates()
        first = candidates.steps[0].batch
        omitted = candidates.steps[-1]
        payload = self._candidate_submission(candidates.steps[:-1])
        payload[first.label][first.workflow_alias]["inspect"]["evidence"] = ""
        remaining = self.sut.flow_next(payload)
        self.assertIsNone(remaining.error, remaining.error)
        self.assertEqual(len(remaining.steps), 3)
        self.assertIn(omitted.instance_id, {step.instance_id for step in remaining.steps})
        resumed = FlowRunOrchestratorFactory(
            base_dir_resolver=RunsBaseDirResolver(project_dir_fn=lambda: self.root), plugin_root=self.root,
        ).build()
        replayed = resumed.flow_next()
        self.assertEqual([step.instance_id for step in replayed.steps], [step.instance_id for step in remaining.steps])
        finished = resumed.flow_next(self._candidate_submission(replayed.steps))
        self.assertEqual(finished.status, "done", finished.error)
        events = [json.loads(line) for line in (self.root / "runs" / self.run_id / "events.jsonl").read_text().splitlines()]
        completed = [event["instance_id"] for event in events if event["event"] == "step_completed"
                     and event["instance_id"] in {step.instance_id for step in candidates.steps}]
        self.assertEqual(len(completed), 10)
        self.assertEqual(len(set(completed)), 10)

    def _start_candidates(self):
        started = self.sut.flow_start(str(self.workflow))
        self.run_id = started.run_id
        targets = self.sut.flow_next({started.steps[0].instance_id: {"targets": ["A", "B"]}})
        discovered = {}
        for step in targets.steps:
            self.assertIsInstance(step.batch, AggregateBatchStepPresentation)
            label = step.batch.label
            names = ["Shared", "Second", "Third"] if label == "A" else ["Shared", "Second"]
            discovered.setdefault(label, {}).setdefault(step.batch.workflow_alias, {})[
                step.batch.authored_step.step_id
            ] = {"candidates": [{"name": name} for name in names]}

        return self.sut.flow_next(discovered)

    @staticmethod
    def _candidate_submission(steps):
        submission = {}
        for step in steps:
            batch = step.batch
            field = "evidence" if batch.authored_step.step_id == "inspect" else "result"
            submission.setdefault(batch.label, {}).setdefault(batch.workflow_alias, {})[
                batch.authored_step.step_id
            ] = {field: step.instance_id}

        return submission

    def test_execution_presentation_matrix_preserves_all_original_outputs(self) -> None:
        self._write("pair", """
            id: pair
            name: Pair
            max_turns: 20
            steps:
              - id: inspect
                prompt: Inspect {{params.item}}.
                outputs: [{name: result, type: data, schema: {type: string}}]
              - id: classify
                depends_on: [inspect]
                prompt: Classify the inspected item.
                outputs: [{name: result, type: data, schema: {type: string}}]
        """)
        for execution, presentation, iteration, expected in [
            ("granular", "individual", "omitted", 4), ("aggregate", "individual", "omitted", 2),
            ("granular", "combined", "omitted", 2), ("aggregate", "combined", "omitted", 1),
            ("granular", "combined", "individual", 4), ("aggregate", "combined", "individual", 2),
        ]:
            with self.subTest(execution=execution, presentation=presentation, iteration=iteration):
                for_each = ('"{{steps.prepare.outputs.items}}"' if iteration == "omitted"
                            else '{source: "{{steps.prepare.outputs.items}}", mode: individual}')
                workflow = self._write(f"{execution}-{presentation}-{iteration}", f"""
                    id: {execution}-{presentation}-{iteration}
                    name: Matrix
                    max_turns: 20
                    steps:
                      - id: prepare
                        prompt: Prepare.
                        outputs: [{{name: items, type: data, schema: {{type: array, items: {{type: string}}}}}}]
                      - group: phase
                        execution: {{mode: {execution}}}
                        presentation: {{mode: {presentation}}}
                        steps:
                          - include: {{workflow: pair}}
                            as: pair
                            depends_on: [prepare]
                            for_each: {for_each}
                            with:
                              item: "{{{{item}}}}"
                """)
                started = self.sut.flow_start(str(workflow))
                current = self.sut.flow_next({started.steps[0].instance_id: {"items": ["A", "B"]}})
                submissions = 0
                while current.status != "done" and submissions < 5:
                    self.assertIsNone(current.error, current.error)
                    payload = {}
                    for step in SiblingBatchStepSelectorFactory().make().select(current.steps[0], current.steps):
                        result = {"result": step.instance_id}
                        batch = step.batch
                        if isinstance(batch, AggregateBatchStepPresentation):
                            payload.setdefault(batch.label, {}).setdefault(batch.workflow_alias, {})[batch.authored_step.step_id] = result
                        elif isinstance(batch, CombinedRuleBatchStepPresentation):
                            payload.setdefault(batch.label, {})[batch.rule_alias] = result
                        elif batch is not None:
                            payload[batch.label] = result
                        else:
                            payload[step.instance_id] = result
                    current = self.sut.flow_next(payload)
                    submissions += 1
                self.assertEqual(current.status, "done", current.error)
                self.assertEqual(submissions, expected)
                events = [json.loads(line) for line in (self.root / "runs" / started.run_id / "events.jsonl").read_text().splitlines()]
                completed = [event for event in events if event["event"] == "step_completed" and event["step_id"] != "prepare"]
                self.assertEqual(len(completed), 4)
                for event in completed:
                    self.assertEqual(event["outputs"]["result"], event["instance_id"])

    def test_pending_prompt_binding_waits_for_validated_output(self) -> None:
        workflow = self._write("bound-prompt", """
            id: bound-prompt
            name: Bound prompt
            max_turns: 5
            execution: {mode: aggregate}
            presentation: {mode: combined}
            steps:
              - id: choose
                prompt: Choose a value.
                outputs: [{name: value, type: data, schema: {type: string}}]
              - id: explain
                depends_on: [choose]
                prompt: Explain {{steps.choose.outputs.value}}.
                outputs: [{name: result, type: data, schema: {type: string}}]
        """)
        started = self.sut.flow_start(str(workflow))
        self.assertEqual([step.step_id for step in started.steps], ["choose"])
        batch = started.steps[0].batch
        explained = self.sut.flow_next({batch.label: {batch.workflow_alias: {"choose": {"value": "chosen"}}}})
        self.assertEqual([step.step_id for step in explained.steps], ["explain"])
        self.assertIn("Explain chosen.", explained.steps[0].prompt)

    def _write(self, name: str, contents: str) -> Path:
        package = self.root / "workflows" / name
        package.mkdir(parents=True)
        path = package / "workflow.yaml"
        path.write_text(textwrap.dedent(contents), encoding="utf-8")
        return path
