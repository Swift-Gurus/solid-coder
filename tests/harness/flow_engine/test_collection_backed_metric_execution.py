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
solid-spec: [SPEC-053, SPEC-054]
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

    def test_counts_projected_child_workflow_outputs_without_model_fan_in(self) -> None:
        child = self.project_root / "child.yaml"
        child.write_text(
            textwrap.dedent(
                """
                id: child-analysis
                name: Child Analysis
                outputs:
                  - name: assessment
                    type: data
                    value: "{{steps.analyze.outputs.assessment}}"
                    schema:
                      type: object
                      additionalProperties: false
                      required: [classification]
                      properties:
                        classification: {type: string}
                steps:
                  - id: analyze
                    prompt: Analyze the candidate.
                    outputs:
                      - name: assessment
                        type: data
                        schema:
                          type: object
                          additionalProperties: false
                          required: [classification]
                          properties:
                            classification: {type: string}
                """
            ),
            encoding="utf-8",
        )
        parent = self.project_root / "parent.yaml"
        parent.write_text(
            textwrap.dedent(
                """
                id: parent-review
                name: Parent Review
                max_turns: 5
                rule: {}
                steps:
                  - include: ./child.yaml
                    as: analyses
                  - id: matching_count
                    type: metric
                    metric_id: TEST-1
                    depends_on: [analyses]
                    value: {type: integer, minimum: 0}
                    scoring:
                      source: "{{workflows.analyses.outputs.assessment}}"
                      when:
                        ref: "{{item.classification}}"
                        equals: MATCH
                      severe: {operator: greater_than_or_equal, value: 1}
                  - id: classify_exception
                    type: exception
                    depends_on: [matching_count]
                    prompt: Classify the whole-rule exception.
                """
            ),
            encoding="utf-8",
        )

        child_step = self.engine.flow_start(str(parent))
        exception = self.engine.flow_next({
            child_step.steps[0].instance_id: {
                "assessment": {"classification": "MATCH"}
            }
        })

        self.assertEqual([step.step_id for step in exception.steps], ["classify_exception"])
        metric_event = next(
            event
            for event in self._events(child_step.run_id)
            if event.get("step_id") == "matching_count"
        )
        self.assertEqual(metric_event["outputs"]["value"], 1)
        self.assertEqual(
            metric_event["metric_derivation"]["source"],
            {
                "kind": "workflow_output",
                "workflow_alias": "analyses",
                "output_name": "assessment",
            },
        )

    def test_nested_rule_instances_score_only_their_projected_children(self) -> None:
        parent_path = self._write_nested_projection_rule_workflows()
        prepared = self.engine.flow_start(str(parent_path))
        candidate_preparations = self.engine.flow_next({
            prepared.steps[0].instance_id: {
                "units": [{"name": "Alpha"}, {"name": "Beta"}],
            }
        })

        candidate_reviews = self.engine.flow_next({
            step.instance_id: {
                "candidates": (
                    [{"name": "Alpha-1"}, {"name": "Alpha-2"}]
                    if "reviews-1" in step.step_id
                    else [{"name": "Beta-1"}]
                )
            }
            for step in candidate_preparations.steps
        })
        exceptions = self.engine.flow_next({
            step.instance_id: {
                "assessment": {
                    "classification": (
                        "MISS" if "Alpha-2" in step.prompt else "MATCH"
                    )
                }
            }
            for step in candidate_reviews.steps
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
            and event.get("step_id", "").endswith("matching_count")
        ]
        self.assertEqual(
            [event["outputs"]["value"] for event in metric_events],
            [1, 1],
        )
        self.assertEqual(
            [event["workflow_instance_id"] for event in metric_events],
            ["reviews-1", "reviews-2"],
        )

        replayed = self._engine().flow_next()

        self.assertEqual(
            [step.step_id for step in replayed.steps],
            ["reviews-1.classify_exception", "reviews-2.classify_exception"],
        )
        replayed_metric_events = [
            event
            for event in self._events(prepared.run_id)
            if event.get("event") == "step_completed"
            and event.get("step_id", "").endswith("matching_count")
        ]
        self.assertEqual(len(replayed_metric_events), 2)

    def test_batch_for_each_derives_one_instance_scoped_metric_per_item(self) -> None:
        parent_path = self._write_dynamic_rule_workflows(batch=True)
        prepared = self.engine.flow_start(str(parent_path))
        analyses = self.engine.flow_next({
            prepared.steps[0].instance_id: {
                "units": [{"name": "Alpha"}, {"name": "Beta"}],
            }
        })

        self.assertEqual(
            [step.batch.label for step in analyses.steps],
            ["Alpha", "Beta"],
        )
        exceptions = self.engine.flow_next({
            "Alpha": {
                "task_sites": [
                    {"classification": "DETACHED", "is_exception": False},
                ],
            },
            "Beta": {
                "task_sites": [
                    {"classification": "DETACHED", "is_exception": False},
                    {"classification": "DETACHED", "is_exception": False},
                ],
            },
        })

        self.assertEqual(
            [step.batch.label for step in exceptions.steps],
            ["Alpha", "Beta"],
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

        completed = self.engine.flow_next({
            "Alpha": {
                "is_exception": False,
                "additional_info": {
                    "reasoning": "Alpha is not exempt.",
                    "evidence": "Alpha performs runtime behavior.",
                },
            },
            "Beta": {
                "is_exception": False,
                "additional_info": {
                    "reasoning": "Beta is not exempt.",
                    "evidence": "Beta performs runtime behavior.",
                },
            },
        })

        self.assertEqual(completed.status, "done", completed.error)

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

    def test_aggregate_execution_drains_reducer_without_model_metric_step(self) -> None:
        workflow_path = self.project_root / "aggregate-maximum.yaml"
        workflow_path.write_text(
            textwrap.dedent(self._maximum_workflow()).replace(
                "max_turns: 5",
                "max_turns: 5\nexecution:\n  mode: aggregate",
                1,
            ),
            encoding="utf-8",
        )
        started = self.engine.flow_start(str(workflow_path))

        self.assertEqual(len(started.steps), 1)
        self.assertNotIn("maximum_depth", started.steps[0].prompt)
        advanced = self.engine.flow_next({
            "maximum-depth-review": {
                "maximum-depth-review": {
                    "analyze_views": {
                        "views": [
                            {"depth": 2, "is_exception": False},
                            {"depth": 5, "is_exception": False},
                        ]
                    }
                }
            }
        })

        self.assertIsNone(advanced.error, advanced.error)
        self.assertEqual(len(advanced.steps), 1)
        self.assertNotIn("maximum_depth", advanced.steps[0].prompt)
        completed = self.engine.flow_next({
            "maximum-depth-review": {
                "maximum-depth-review": {
                    "classify_exception": {
                        "is_exception": False,
                        "additional_info": {
                            "reasoning": "No exception applies.",
                            "evidence": "The unit contains runtime behavior.",
                        },
                    }
                }
            }
        })

        self.assertEqual(completed.status, "done", completed.error)
        result = self._result(started.run_id, "maximum-depth-review")
        self.assertEqual(result["metrics"][0]["value"], 5)
        self.assertEqual(
            result["metrics"][0]["derivation"]["reducer"]["type"],
            "maximum",
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

    def test_reduces_and_replays_maximum_with_projection_evidence(self) -> None:
        workflow_path = self.project_root / "maximum.yaml"
        workflow_path.write_text(
            textwrap.dedent(self._maximum_workflow()),
            encoding="utf-8",
        )
        started = self.engine.flow_start(str(workflow_path))

        advanced = self.engine.flow_next({
            started.steps[0].instance_id: {
                "views": [
                    {"depth": 2, "is_exception": False},
                    {"depth": 9, "is_exception": True},
                    {"depth": 5, "is_exception": False},
                ]
            }
        })

        self.assertIsNone(advanced.error, advanced.error)
        metric_event = next(
            event
            for event in self._events(started.run_id)
            if event.get("step_id") == "maximum_depth"
        )
        self.assertEqual(metric_event["outputs"]["value"], 5)
        self.assertIn(
            "maximum reducer",
            metric_event["outputs"]["additional_info"]["reasoning"],
        )
        derivation = metric_event["metric_derivation"]
        self.assertEqual(derivation["kind"], "collection_reducer")
        self.assertEqual(derivation["reducer"]["type"], "maximum")
        self.assertEqual(
            derivation["projection_evidence"],
            [{"index": 0, "value": 2}, {"index": 2, "value": 5}],
        )

        replayed = self._engine().flow_next()

        self.assertIsNone(replayed.error, replayed.error)
        metric_events = [
            event
            for event in self._events(started.run_id)
            if event.get("step_id") == "maximum_depth"
        ]
        self.assertEqual(len(metric_events), 1)

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

    def _result(
        self,
        run_id: str,
        workflow_id: str = "detached-task-review",
    ) -> dict:
        result_path = (
            self.project_root
            / "runs"
            / run_id
            / "results"
            / "review"
            / workflow_id
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

    def _maximum_workflow(self) -> str:
        return """
        id: maximum-depth-review
        name: Maximum Depth Review
        max_turns: 5
        rule: {}
        steps:
          - id: analyze_views
            prompt: Classify view depths.
            outputs:
              - name: views
                type: data
                schema:
                  type: array
                  items:
                    type: object
                    additionalProperties: false
                    required: [depth, is_exception]
                    properties:
                      depth: {type: integer}
                      is_exception: {type: boolean}
          - id: maximum_depth
            type: metric
            metric_id: DEPTH-1
            depends_on: [analyze_views]
            value: {type: integer, minimum: 0}
            scoring:
              source: "{{steps.analyze_views.outputs.views}}"
              when:
                ref: "{{item.is_exception}}"
                equals: false
              reducer:
                type: maximum
                value: "{{item.depth}}"
              severe: {operator: greater_than_or_equal, value: 5}
          - id: classify_exception
            type: exception
            depends_on: [maximum_depth]
            prompt: Classify the whole-rule exception.
        """

    def _write_dynamic_rule_workflows(self, batch: bool = False) -> Path:
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
        parent_workflow = textwrap.dedent(
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
                    __FOR_EACH__
            """
        )
        for_each = (
            "for_each:\n"
            '      source: "{{steps.prepare.outputs.units}}"\n'
            "      mode: batch\n"
            '      label: "{{item.name}}"'
            if batch
            else 'for_each: "{{steps.prepare.outputs.units}}"'
        )
        parent_path.write_text(
            parent_workflow.replace("__FOR_EACH__", for_each),
            encoding="utf-8",
        )
        return parent_path

    def _write_nested_projection_rule_workflows(self) -> Path:
        workflow_root = self.project_root / "workflows" / "review"
        candidate_path = workflow_root / "candidate-analysis" / "workflow.yaml"
        candidate_path.parent.mkdir(parents=True, exist_ok=True)
        candidate_path.write_text(
            textwrap.dedent(
                """
                id: candidate-analysis
                name: Candidate Analysis
                max_turns: 5
                outputs:
                  - name: assessment
                    type: data
                    value: "{{steps.analyze.outputs.assessment}}"
                    schema:
                      type: object
                      additionalProperties: false
                      required: [classification]
                      properties:
                        classification: {type: string}
                steps:
                  - id: analyze
                    prompt: Analyze {{params.candidate.name}}.
                    outputs:
                      - name: assessment
                        type: data
                        schema:
                          type: object
                          additionalProperties: false
                          required: [classification]
                          properties:
                            classification: {type: string}
                """
            ),
            encoding="utf-8",
        )
        rule_path = workflow_root / "nested-projection-rule" / "workflow.yaml"
        rule_path.parent.mkdir(parents=True, exist_ok=True)
        rule_path.write_text(
            textwrap.dedent(
                """
                id: nested-projection-rule
                name: Nested Projection Rule
                max_turns: 10
                rule: {}
                steps:
                  - id: prepare_candidates
                    prompt: Prepare candidates.
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
                  - include:
                      workflow: candidate-analysis
                    as: analyses
                    depends_on: [prepare_candidates]
                    for_each: "{{steps.prepare_candidates.outputs.candidates}}"
                    with:
                      candidate: "{{item}}"
                  - id: matching_count
                    type: metric
                    metric_id: NESTED-1
                    depends_on: [analyses]
                    value: {type: integer, minimum: 0}
                    scoring:
                      source: "{{workflows.analyses.outputs.assessment}}"
                      when:
                        ref: "{{item.classification}}"
                        equals: MATCH
                      severe: {operator: greater_than_or_equal, value: 1}
                  - id: classify_exception
                    type: exception
                    depends_on: [matching_count]
                    prompt: Classify the whole-rule exception.
                """
            ),
            encoding="utf-8",
        )
        parent_path = workflow_root / "nested-projection-parent" / "workflow.yaml"
        parent_path.parent.mkdir(parents=True, exist_ok=True)
        parent_path.write_text(
            textwrap.dedent(
                """
                id: nested-projection-parent
                name: Nested Projection Parent
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
                            required: [name]
                            properties:
                              name: {type: string}
                  - include:
                      workflow: nested-projection-rule
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
