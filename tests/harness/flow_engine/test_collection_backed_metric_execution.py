"""Tests deterministic execution of collection-backed metric steps."""

import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from harness.flow_run_orchestrator_factory import FlowRunOrchestratorFactory
from harness.runs_base_dir_resolver import RunsBaseDirResolver


"""
solid-name: TestCollectionBackedMetricExecution
solid-category: integration-test
solid-spec: [SPEC-053]
solid-description: Verifies deterministic collection metric completion through the real flow engine.
"""
class TestCollectionBackedMetricExecution(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project_root = Path(temporary.name)
        self.workflow_path = self.project_root / "workflow.yaml"
        self.workflow_path.write_text(
            textwrap.dedent(self._workflow()),
            encoding="utf-8",
        )
        self.engine = FlowRunOrchestratorFactory(
            base_dir_resolver=RunsBaseDirResolver(
                project_dir_fn=lambda: self.project_root
            ),
            plugin_root=self.project_root,
        ).build()

    def test_counts_matching_entries_without_requesting_metric_submission(self) -> None:
        started = self.engine.flow_start(str(self.workflow_path))

        advanced = self.engine.flow_next({
            started.steps[0].instance_id: {
                "task_sites": [
                    {"classification": "DETACHED", "is_exception": False},
                    {"classification": "STRUCTURED", "is_exception": False},
                    {"classification": "DETACHED", "is_exception": True},
                    {"classification": "DETACHED", "is_exception": False},
                ]
            }
        })

        self.assertIsNone(advanced.error, advanced.error)
        self.assertEqual(
            [step.step_id for step in advanced.steps],
            ["classify_exception"],
        )
        metric_event = next(
            event
            for event in self._events(started.run_id)
            if event.get("event") == "step_completed"
            and event.get("step_id") == "detached_task_count"
        )
        self.assertEqual(metric_event["session_id"], "engine")
        self.assertEqual(metric_event["outputs"]["value"], 2)
        self.assertIn(
            "2 of 4",
            metric_event["outputs"]["additional_info"]["reasoning"],
        )
        self.assertIn(
            "[0, 3]",
            metric_event["outputs"]["additional_info"]["evidence"],
        )
        self.assertFalse(metric_event["empty_collection"])
        derivation = metric_event["metric_derivation"]
        self.assertEqual(derivation["kind"], "collection_count")
        self.assertEqual(
            derivation["source"],
            {
                "step_id": "analyze_task_sites",
                "output_name": "task_sites",
            },
        )
        self.assertEqual(derivation["source_size"], 4)
        self.assertEqual(derivation["matched_indexes"], [0, 3])
        self.assertEqual(derivation["excluded_indexes"], [1, 2])
        self.assertEqual(len(derivation["condition_evidence"]), 4)

        replayed = self._engine().flow_next()

        self.assertIsNone(replayed.error, replayed.error)
        self.assertEqual(
            [step.step_id for step in replayed.steps],
            ["classify_exception"],
        )
        metric_events = [
            event
            for event in self._events(started.run_id)
            if event.get("event") == "step_completed"
            and event.get("step_id") == "detached_task_count"
        ]
        self.assertEqual(len(metric_events), 1)

        completed = self.engine.flow_next({
            advanced.steps[0].instance_id: {
                "is_exception": False,
                "additional_info": {
                    "reasoning": "No whole-rule exception applies.",
                    "evidence": "The reviewed unit performs runtime behavior.",
                },
            }
        })

        self.assertEqual(completed.status, "done")
        result = self._result(started.run_id)
        decision_derivation = result["metrics"][0]["derivation"]
        self.assertEqual(
            decision_derivation["source"],
            {
                "step_id": "analyze_task_sites",
                "output_name": "task_sites",
            },
        )
        self.assertEqual(decision_derivation["source_size"], 4)
        self.assertEqual(decision_derivation["matched_indexes"], [0, 3])
        self.assertEqual(decision_derivation["excluded_indexes"], [1, 2])

    def test_counts_only_instance_local_entries_in_dynamic_rule_includes(self) -> None:
        parent_path = self._write_dynamic_rule_workflows()
        prepared = self.engine.flow_start(str(parent_path))
        analyses = self.engine.flow_next({
            prepared.steps[0].instance_id: {
                "units": [{"name": "Alpha"}, {"name": "Beta"}],
            }
        })

        exceptions = self.engine.flow_next({
            analyses.steps[0].instance_id: {
                "task_sites": [
                    {"classification": "DETACHED", "is_exception": False},
                    {"classification": "STRUCTURED", "is_exception": False},
                ],
            },
            analyses.steps[1].instance_id: {
                "task_sites": [
                    {"classification": "DETACHED", "is_exception": False},
                    {"classification": "DETACHED", "is_exception": False},
                    {"classification": "DETACHED", "is_exception": True},
                ],
            },
        })

        self.assertIsNone(exceptions.error, exceptions.error)
        self.assertEqual(
            [step.step_id for step in exceptions.steps],
            ["reviews-1.classify_exception", "reviews-2.classify_exception"],
        )
        metric_events = [
            event
            for event in self._events(prepared.run_id)
            if event.get("event") == "step_completed"
            and event.get("metric_derivation") is not None
        ]
        self.assertEqual(
            [event["outputs"]["value"] for event in metric_events],
            [1, 2],
        )
        self.assertEqual(
            [event["workflow_instance_id"] for event in metric_events],
            ["reviews-1", "reviews-2"],
        )

    def test_aggregate_execution_omits_internal_metric_and_preserves_exception_audit(self) -> None:
        workflow_path = self.project_root / "aggregate.yaml"
        workflow_path.write_text(
            textwrap.dedent(self._workflow()).replace(
                "max_turns: 5",
                "max_turns: 5\nexecution:\n  mode: aggregate",
                1,
            ),
            encoding="utf-8",
        )
        started = self.engine.flow_start(str(workflow_path))

        self.assertEqual(len(started.steps), 1)
        self.assertNotIn("detached_task_count", started.steps[0].prompt)
        advanced = self.engine.flow_next({
            "detached-task-review": {
                "detached-task-review": {
                    "analyze_task_sites": {
                        "task_sites": [
                            {
                                "classification": "DETACHED",
                                "is_exception": False,
                            }
                        ]
                    }
                }
            }
        })

        self.assertIsNone(advanced.error, advanced.error)
        self.assertEqual(len(advanced.steps), 1)
        self.assertNotIn("detached_task_count", advanced.steps[0].prompt)
        completed = self.engine.flow_next({
            "detached-task-review": {
                "detached-task-review": {
                    "classify_exception": {
                        "is_exception": True,
                        "additional_info": {
                            "reasoning": "The whole rule is exempt.",
                            "evidence": "The unit is a pure data carrier.",
                        },
                    }
                }
            }
        })

        self.assertEqual(completed.status, "done", completed.error)
        result = self._result(started.run_id)
        self.assertEqual(result["severity"], "COMPLIANT")
        self.assertEqual(result["metrics"][0]["severity"], "COMPLIANT")
        self.assertEqual(result["metrics"][0]["raw_severity"], "SEVERE")
        self.assertEqual(result["metrics"][0]["value"], 1)
        self.assertEqual(
            result["metrics"][0]["matching_band"],
            {"operator": "greater_than_or_equal", "value": 1},
        )
        self.assertEqual(
            result["metrics"][0]["derivation"]["matched_indexes"],
            [0],
        )

    def test_skipped_source_completes_internal_metric_with_zero(self) -> None:
        workflow_path = self.project_root / "skipped-source.yaml"
        workflow_path.write_text(
            textwrap.dedent(self._workflow()).replace(
                "    prompt: Classify every task site.",
                (
                    "    prompt: Classify every task site.\n"
                    "    when:\n"
                    '      ref: "{{params.enabled}}"\n'
                    "      equals: true"
                ),
                1,
            ),
            encoding="utf-8",
        )

        ready = self.engine.flow_start(
            str(workflow_path),
            params={"enabled": False},
        )

        self.assertIsNone(ready.error, ready.error)
        self.assertEqual(
            [step.step_id for step in ready.steps],
            ["classify_exception"],
        )
        metric_event = next(
            event
            for event in self._events(ready.run_id)
            if event.get("step_id") == "detached_task_count"
        )
        self.assertEqual(metric_event["outputs"]["value"], 0)
        self.assertEqual(metric_event["metric_derivation"]["source_size"], 0)
        self.assertEqual(metric_event["metric_derivation"]["matched_indexes"], [])

    def test_resume_completes_missing_internal_derivation_exactly_once(self) -> None:
        started = self.engine.flow_start(str(self.workflow_path))
        self.engine.flow_next({
            started.steps[0].instance_id: {
                "task_sites": [
                    {"classification": "DETACHED", "is_exception": False}
                ]
            }
        })
        events_path = self.project_root / "runs" / started.run_id / "events.jsonl"
        preserved_events = [
            event
            for event in self._events(started.run_id)
            if not (
                event.get("step_id") == "detached_task_count"
                or event.get("instance_id") == "detached_task_count-1"
            )
        ]
        events_path.write_text(
            "".join(f"{json.dumps(event)}\n" for event in preserved_events),
            encoding="utf-8",
        )

        resumed = self._engine().flow_next()

        self.assertIsNone(resumed.error, resumed.error)
        self.assertEqual(
            [step.step_id for step in resumed.steps],
            ["classify_exception"],
        )
        metric_events = [
            event
            for event in self._events(started.run_id)
            if event.get("event") == "step_completed"
            and event.get("step_id") == "detached_task_count"
        ]
        self.assertEqual(len(metric_events), 1)
        self.assertEqual(metric_events[0]["outputs"]["value"], 1)

    def _engine(self):
        return FlowRunOrchestratorFactory(
            base_dir_resolver=RunsBaseDirResolver(
                project_dir_fn=lambda: self.project_root
            ),
            plugin_root=self.project_root,
        ).build()

    def _events(self, run_id: str) -> list[dict]:
        events_path = self.project_root / "runs" / run_id / "events.jsonl"
        return [
            json.loads(line)
            for line in events_path.read_text(encoding="utf-8").splitlines()
        ]

    def _result(self, run_id: str) -> dict:
        result_path = (
            self.project_root
            / "runs"
            / run_id
            / "results"
            / "review"
            / "detached-task-review"
            / run_id
            / "result.json"
        )
        return json.loads(result_path.read_text(encoding="utf-8"))

    def _workflow(self) -> str:
        return """
        id: detached-task-review
        name: Detached Task Review
        max_turns: 5
        rule: {}
        steps:
          - id: analyze_task_sites
            prompt: Classify every task site.
            outputs:
              - name: task_sites
                type: data
                schema:
                  type: array
                  items:
                    type: object
                    additionalProperties: false
                    required: [classification, is_exception]
                    properties:
                      classification:
                        type: string
                        enum: [DETACHED, STRUCTURED]
                      is_exception: {type: boolean}
          - id: detached_task_count
            type: metric
            metric_id: DT-1
            depends_on: [analyze_task_sites]
            value: {type: integer, minimum: 0}
            scoring:
              source: "{{steps.analyze_task_sites.outputs.task_sites}}"
              when:
                all:
                  - ref: "{{item.classification}}"
                    equals: DETACHED
                  - ref: "{{item.is_exception}}"
                    equals: false
              severe: {operator: greater_than_or_equal, value: 1}
          - id: classify_exception
            type: exception
            depends_on: [detached_task_count]
            prompt: Classify the whole-rule exception.
        """

    def _write_dynamic_rule_workflows(self) -> Path:
        workflow_root = self.project_root / "workflows" / "review"
        child_path = (
            workflow_root
            / "child-detached-task-review"
            / "workflow.yaml"
        )
        child_path.parent.mkdir(parents=True, exist_ok=True)
        child_path.write_text(
            textwrap.dedent(self._workflow()).replace(
                "id: detached-task-review",
                "id: child-detached-task-review",
                1,
            ),
            encoding="utf-8",
        )
        parent_path = workflow_root / "parent" / "workflow.yaml"
        parent_path.parent.mkdir(parents=True, exist_ok=True)
        parent_path.write_text(
            textwrap.dedent(
                """
                id: parent-review
                name: Parent Review
                max_turns: 10
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
                            required: [name]
                            properties:
                              name: {type: string}
                  - include:
                      workflow: child-detached-task-review
                    as: reviews
                    depends_on: [prepare]
                    for_each: "{{steps.prepare.outputs.units}}"
                """
            ),
            encoding="utf-8",
        )
        return parent_path


if __name__ == "__main__":
    unittest.main()
