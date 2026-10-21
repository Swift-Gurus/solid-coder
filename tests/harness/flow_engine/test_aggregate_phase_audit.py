"""Exercises phase-split diagnostics without changing workflow execution."""

import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from harness.flow_engine_assembly_factory import FlowEngineAssemblyFactory
from harness.flow_run_orchestrator_factory import FlowRunOrchestratorFactory
from harness.runs_base_dir_resolver import RunsBaseDirResolver


"""
solid-name: TestAggregatePhaseAudit
solid-category: unit-test
solid-spec: [SPEC-067]
solid-description: Proves durable planning diagnostics explain phase splits without changing prompts, retries, or replayed execution state.
"""
class TestAggregatePhaseAudit(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.sut = self._engine()

    def _engine(self):
        return FlowRunOrchestratorFactory(
            base_dir_resolver=RunsBaseDirResolver(project_dir_fn=lambda: self.root),
            plugin_root=self.root,
        ).build()

    def _start(self, steps):
        workflow = self.root / "workflow.yaml"
        workflow.write_text(
            "id: audit\nname: Audit\nmax_turns: 10\n"
            "execution: {mode: aggregate}\npresentation: {mode: combined}\nsteps:\n"
            + textwrap.dedent(steps), encoding="utf-8",
        )
        result = self.sut.flow_start(str(workflow))
        self.assertIsNone(result.error, result.error)
        self.events = self.root / "runs" / result.run_id / "events.jsonl"
        return result

    def _audits(self):
        return [event["audit"] for event in map(json.loads, self.events.read_text().splitlines())
                if event["event"] == "aggregate_phase_planned"]

    def test_pending_bindings_are_audited_without_prompt_leaks_or_replay_changes(self):
        started = self._start("""
          - id: choose
            prompt: Choose.
            outputs: [{name: value, type: data, schema: {type: string, minLength: 1}}]
          - id: explain
            depends_on: [choose]
            prompt: Explain {{steps.choose.outputs.value}}.
            outputs: [{name: value, type: data, schema: {type: string}}]
          - id: conclude
            depends_on: [explain]
            prompt: Conclude.
            outputs: [{name: value, type: data, schema: {type: string}}]
        """)
        self.assertEqual([step.step_id for step in started.steps], ["choose"])
        self.assertEqual(len(self._audits()), 1)
        phase = self._audits()[0]["phases"][0]
        self.assertEqual(phase["instance_ids"], ["choose-1"])
        self.assertEqual([(item["step_id"], item["reason"]) for item in phase["deferrals"]],
                         [("explain", "unavailable_render_input"), ("conclude", "pending_validation")])
        self.assertEqual(phase["deferrals"][1]["blocking_step_ids"], ["explain"])
        self.assertEqual(started.steps[0].batch.authored_step.prompt, "Choose.")
        self.assertNotIn("unavailable_render_input", str(started))
        replayer = FlowEngineAssemblyFactory().build().event_replayer
        before = replayer.replay(str(self.events))
        resumed = self._engine().flow_next()
        self.assertEqual(resumed.steps, started.steps)
        self.assertEqual(replayer.replay(str(self.events)), before)
        self.assertEqual(len(self._audits()), 1)
        batch = started.steps[0].batch
        rejected = self.sut.flow_next({batch.label: {batch.workflow_alias: {"choose": {"value": ""}}}})
        self.assertIsNotNone(rejected.steps[0].rejection_reason)
        completed = self.sut.flow_next({batch.label: {batch.workflow_alias: {"choose": {"value": "chosen"}}}})
        self.assertEqual([step.step_id for step in completed.steps], ["explain", "conclude"])
        self.assertEqual(self._audits()[-1]["phases"][0]["deferrals"], [])

    def test_engine_condition_and_collection_barriers_explain_only_deferred_work(self):
        started = self._start("""
          - id: choose
            prompt: Choose.
            outputs: [{name: items, type: data, schema: {type: array, items: {type: string}}}]
          - id: calculate
            type: operation
            operation: collection.count
            depends_on: [choose]
            with: {values: "{{steps.choose.outputs.items}}"}
          - id: report
            depends_on: [calculate]
            prompt: Report.
          - id: conditional
            depends_on: [choose]
            when: {ref: "{{steps.choose.outputs.items}}", equals: []}
            prompt: Conditional.
          - id: review
            depends_on: [choose]
            for_each: "{{steps.choose.outputs.items}}"
            prompt: Review {{item}}.
          - id: independent
            prompt: Independent.
        """)
        self.assertEqual([step.step_id for step in started.steps], ["choose", "independent"])
        self.assertEqual(len(self._audits()), 1)
        splits = self._audits()[0]["phases"][0]["deferrals"]
        self.assertEqual([(item["step_id"], item["reason"]) for item in splits], [
            ("calculate", "engine_owned_step"), ("report", "pending_validation"),
            ("conditional", "unavailable_condition"), ("review", "unavailable_collection"),
        ])
        self.assertEqual(splits[1]["blocking_step_ids"], ["calculate"])

    def test_nested_explicit_policy_boundaries_preserve_their_scope(self):
        started = self._start("""
          - id: outside
            prompt: Outside.
          - group: child
            execution: {mode: granular}
            presentation: {mode: combined}
            steps:
              - id: first
                prompt: First.
                outputs: [{name: value, type: data, schema: {type: string}}]
              - id: second
                depends_on: [first]
                prompt: Second.
        """)
        audit = self._audits()[0]
        self.assertEqual(audit["root_execution"], "aggregate")
        scope = next(scope for scope in audit["policy_scopes"] if scope["alias"] == "child")
        self.assertEqual(scope["execution"], "granular")
        self.assertTrue(scope["execution_declared"])
        child_phase = next(phase for phase in audit["phases"] if phase["boundary_id"] != "audit")
        policy_split = next(item for item in child_phase["deferrals"] if item["reason"] == "execution_policy")
        self.assertTrue(policy_split["step_id"].endswith("second"))
        self.assertEqual(policy_split["boundary_id"], child_phase["boundary_id"])
        self.assertFalse(any(step.step_id.endswith("second") for step in started.steps))

    def test_partial_fan_out_names_pending_parent_and_keeps_accepted_instances_closed(self):
        started = self._start("""
          - id: prepare
            prompt: Prepare.
            outputs: [{name: items, type: data, schema: {type: array, items: {type: string}}}]
          - id: review
            depends_on: [prepare]
            for_each: {source: "{{steps.prepare.outputs.items}}", mode: batch, label: "{{item}}"}
            prompt: Review {{item}}.
            outputs: [{name: value, type: data, schema: {type: string}}]
          - id: summarize
            depends_on: [review]
            prompt: Summarize.
        """)
        prepared = started.steps[0].batch
        reviews = self.sut.flow_next({prepared.label: {prepared.workflow_alias: {"prepare": {"items": ["A", "B"]}}}})
        first, second = reviews.steps
        batch = first.batch
        remaining = self.sut.flow_next({batch.label: {batch.workflow_alias: {"review": {"value": "A"}}}})
        self.assertEqual([step.instance_id for step in remaining.steps], [second.instance_id])
        phase = self._audits()[-1]["phases"][0]
        self.assertEqual(phase["instance_ids"], [second.instance_id])
        self.assertEqual(phase["deferrals"][0]["step_id"], "summarize")
        self.assertEqual(phase["deferrals"][0]["blocking_step_ids"], ["review"])
        self.assertEqual(phase["deferrals"][0]["reason"], "pending_validation")
        self.assertEqual(self._engine().flow_next().steps, remaining.steps)
