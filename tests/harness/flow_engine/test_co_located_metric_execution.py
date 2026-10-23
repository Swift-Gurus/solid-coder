"""Tests deterministic execution of co-located metrics."""

import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from harness.batch_step_renderer_factory import BatchStepRendererFactory
from harness.flow_run_orchestrator_factory import FlowRunOrchestratorFactory
from harness.runs_base_dir_resolver import RunsBaseDirResolver

"""
solid-name: TestCoLocatedMetricExecution
solid-category: integration-test
solid-spec: [SPEC-058]
solid-description: Verifies compact metrics drain internally and replay without requesting model-owned metric output.
"""


class TestCoLocatedMetricExecution(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project_root = Path(temporary.name)
        self.workflow_path = self.project_root / "workflow.yaml"
        self.workflow_path.write_text(
            textwrap.dedent(self._workflow()),
            encoding="utf-8",
        )
        self.engine = self._engine()

    def test_drains_metric_after_owner_submission_and_replays_once(self) -> None:
        started = self.engine.flow_start(str(self.workflow_path))

        self.assertEqual([step.step_id for step in started.steps], ["classify"])
        self.assertNotIn("action_count", started.steps[0].prompt)

        exception = self.engine.flow_next(
            {
                started.steps[0].instance_id: {
                    "actions": [
                        {"name": "initialize", "is_lifecycle": True},
                        {"name": "load", "is_lifecycle": False},
                        {"name": "save", "is_lifecycle": False},
                    ]
                }
            }
        )

        self.assertIsNone(exception.error, exception.error)
        self.assertEqual(
            [step.step_id for step in exception.steps],
            ["classify_exception"],
        )
        metric_events = self._metric_events(started.run_id)
        self.assertEqual(len(metric_events), 1)
        self.assertEqual(metric_events[0]["outputs"]["value"], 2)
        self.assertEqual(
            metric_events[0]["metric_derivation"]["matched_indexes"],
            [1, 2],
        )
        replayed = self._engine().flow_next()

        self.assertIsNone(replayed.error, replayed.error)
        self.assertEqual(
            [step.step_id for step in replayed.steps],
            ["classify_exception"],
        )
        self.assertEqual(len(self._metric_events(started.run_id)), 1)

    def test_finalizes_compact_and_explicit_metrics_together(self) -> None:
        self.workflow_path.write_text(
            textwrap.dedent(self._mixed_workflow()),
            encoding="utf-8",
        )
        engine = self._engine()
        started = engine.flow_start(str(self.workflow_path))

        exception = engine.flow_next(
            {
                started.steps[0].instance_id: {
                    "actions": [
                        {"name": "initialize", "is_lifecycle": True},
                        {"name": "load", "is_lifecycle": False},
                        {"name": "save", "is_lifecycle": False},
                    ]
                }
            }
        )

        self.assertEqual(
            [step.step_id for step in exception.steps],
            ["classify_exception"],
        )
        completed = engine.flow_next(
            {
                exception.steps[0].instance_id: {
                    "is_exception": False,
                    "additional_info": {
                        "reasoning": "No rule exception applies.",
                        "evidence": "The unit performs production behavior.",
                    },
                }
            }
        )

        self.assertEqual(completed.status, "done", completed.error)
        result_path = (
            self.project_root
            / "runs"
            / started.run_id
            / "results"
            / "review"
            / "mixed-rule"
            / started.run_id
            / "result.json"
        )
        result = json.loads(result_path.read_text(encoding="utf-8"))
        self.assertEqual(
            [metric["metric_id"] for metric in result["metrics"]],
            ["SRP-1", "SRP-LIFECYCLE"],
        )
        self.assertEqual(
            [metric["value"] for metric in result["metrics"]],
            [2, 1],
        )
        self.assertEqual(
            result["exception"]["additional_info"],
            {
                "reasoning": "No rule exception applies.",
                "evidence": "The unit performs production behavior.",
            },
        )
        scored_events = [
            event
            for event in self._events(started.run_id)
            if event.get("event") == "metric_scored"
            and event.get("metric_id") == "SRP-1"
        ]
        self.assertEqual(len(scored_events), 1)
        self.assertEqual(scored_events[0]["value"], 2)
        self.assertEqual(scored_events[0]["severity"], "SEVERE")
        self.assertEqual(
            scored_events[0]["derivation"]["matched_indexes"],
            [1, 2],
        )

    def test_scores_each_included_workflow_instance_independently(self) -> None:
        parent_path = self._write_dynamic_rule_workflows()
        engine = self._engine()
        prepared = engine.flow_start(str(parent_path))
        analyses = engine.flow_next(
            {
                prepared.steps[0].instance_id: {
                    "units": [{"name": "Alpha"}, {"name": "Beta"}],
                }
            }
        )

        exceptions = engine.flow_next(
            {
                analyses.steps[0].instance_id: {
                    "actions": [
                        {"name": "load", "is_lifecycle": False},
                    ]
                },
                analyses.steps[1].instance_id: {
                    "actions": [
                        {"name": "load", "is_lifecycle": False},
                        {"name": "save", "is_lifecycle": False},
                    ]
                },
            }
        )

        self.assertEqual(
            [step.step_id for step in exceptions.steps],
            [
                "reviews-1.classify_exception",
                "reviews-2.classify_exception",
            ],
        )
        metric_events = [
            event
            for event in self._events(prepared.run_id)
            if event.get("step_id")
            in {"reviews-1.action_count", "reviews-2.action_count"}
        ]
        self.assertEqual(
            [event["outputs"]["value"] for event in metric_events],
            [1, 2],
        )
        self.assertEqual(
            [event["workflow_instance_id"] for event in metric_events],
            ["reviews-1", "reviews-2"],
        )

    def test_drains_metrics_after_combined_aggregate_submission(self) -> None:
        parent_path = self._write_combined_dynamic_rule_workflows()
        engine = self._engine()
        prepared = engine.flow_start(str(parent_path))
        _analyses = engine.flow_next(
            {
                prepared.steps[0].instance_id: {
                    "units": [{"name": "Alpha"}, {"name": "Beta"}],
                }
            }
        )

        exceptions = engine.flow_next(
            {
                "Alpha": {
                    "reviews": {
                        "classify": {
                            "actions": [
                                {"name": "load", "is_lifecycle": False},
                            ]
                        }
                    }
                },
                "Beta": {
                    "reviews": {
                        "classify": {
                            "actions": [
                                {"name": "load", "is_lifecycle": False},
                                {"name": "save", "is_lifecycle": False},
                            ]
                        }
                    }
                },
            }
        )

        self.assertIsNone(exceptions.error, exceptions.error)
        self.assertEqual(
            [step.step_id for step in exceptions.steps],
            [
                "aggregate_rules.reviews-1.classify_exception",
                "aggregate_rules.reviews-2.classify_exception",
            ],
        )
        metric_events = [
            event
            for event in self._events(prepared.run_id)
            if event.get("step_id")
            in {
                "aggregate_rules.reviews-1.action_count",
                "aggregate_rules.reviews-2.action_count",
            }
        ]
        self.assertEqual(
            [event["outputs"]["value"] for event in metric_events],
            [1, 2],
        )

    def test_combines_independent_classifiers_across_co_located_metrics(self) -> None:
        self._write_aggregate_workflow()

        started = self.engine.flow_start(str(self.workflow_path))

        self.assertIsNone(started.error, started.error)
        self.assertEqual(
            [step.step_id for step in started.steps],
            ["classify_actions", "classify_variable_usage", "classify_stakeholders"],
        )
        rendered = BatchStepRendererFactory().make().render(started.steps)
        self.assertEqual(rendered.count("Classify these actions in order"), 1)
        self.assertEqual(rendered.count("Classify these methods in order"), 1)
        self.assertEqual(rendered.count("Classify these stakeholders in order"), 1)
        self.assertNotIn("Engine results:", rendered)
        self.assertNotIn("classify_exception", rendered)
        self.assertNotIn("action_count", rendered)
        self.assertNotIn("cohesion_groups", rendered)
        self.assertNotIn("stakeholder_count", rendered)

    def test_aggregate_metrics_drain_before_dependent_exception_and_replay_once(
        self,
    ) -> None:
        self._write_aggregate_workflow()
        started = self.engine.flow_start(str(self.workflow_path))

        exception = self.engine.flow_next(
            {
                "aggregate-classifiers": {
                    "aggregate-classifiers": {
                        "classify_actions": {
                            "actions": [
                                {"name": "initialize", "is_lifecycle": True},
                                {"name": "load", "is_lifecycle": False},
                                {"name": "save", "is_lifecycle": False},
                            ]
                        },
                        "classify_variable_usage": {
                            "method_variable_usage": [
                                {"method": "load", "variables": ["cache"]},
                                {"method": "save", "variables": ["cache", "storage"]},
                                {"method": "render", "variables": ["view"]},
                            ]
                        },
                        "classify_stakeholders": {
                            "stakeholders": [
                                "Operations",
                                "Presentation",
                            ]
                        },
                    },
                },
            }
        )

        self.assertIsNone(exception.error, exception.error)
        self.assertEqual(
            [step.step_id for step in exception.steps], ["classify_exception"]
        )
        self.assertIn("actions=2", exception.steps[0].prompt)
        self.assertIn("groups=2", exception.steps[0].prompt)
        self.assertIn("stakeholders=2", exception.steps[0].prompt)
        metrics = [
            event
            for event in self._events(started.run_id)
            if event.get("event") == "step_completed"
            and event.get("session_id") == "engine"
        ]
        self.assertEqual(
            [event["step_id"] for event in metrics],
            ["action_count", "cohesion_groups", "stakeholder_count"],
        )
        self.assertEqual([event["outputs"]["value"] for event in metrics], [2, 2, 2])
        self.assertEqual(metrics[0]["metric_derivation"]["matched_indexes"], [1, 2])
        self.assertEqual(
            metrics[1]["metric_derivation"]["component_evidence"]["components"],
            [[0, 1], [2]],
        )
        events_before_replay = self._events(started.run_id)

        restarted = self._engine()
        replayed = restarted.flow_next()

        self.assertIsNone(replayed.error, replayed.error)
        self.assertEqual(
            [step.step_id for step in replayed.steps], ["classify_exception"]
        )
        self.assertEqual(self._events(started.run_id), events_before_replay)
        finished = restarted.flow_next(
            {
                "aggregate-classifiers": {
                    "aggregate-classifiers": {
                        "classify_exception": {
                            "is_exception": False,
                            "additional_info": {
                                "reasoning": "No rule exception applies.",
                                "evidence": "All three engine metrics are two.",
                            },
                        },
                    },
                },
            }
        )
        self.assertEqual(finished.status, "done", finished.error)
        result_path = (
            self.project_root
            / "runs"
            / started.run_id
            / "results/review"
            / "aggregate-classifiers"
            / started.run_id
            / "result.json"
        )
        result = json.loads(result_path.read_text(encoding="utf-8"))
        self.assertEqual(
            [metric["metric_id"] for metric in result["metrics"]],
            ["ACTIONS", "GROUPS", "STAKEHOLDERS"],
        )
        self.assertEqual([metric["value"] for metric in result["metrics"]], [2, 2, 2])
        self.assertEqual(
            [metric["severity"] for metric in result["metrics"]],
            ["SEVERE", "SEVERE", "SEVERE"],
        )

    def test_nested_combined_submission_keeps_three_metrics_scoped_per_target(
        self,
    ) -> None:
        parent_path = self._write_combined_dynamic_rule_workflows()
        self._write_aggregate_workflow()
        child_path = self.project_root / "workflows/review/compact-rule/workflow.yaml"
        child_path.write_text(
            self.workflow_path.read_text(encoding="utf-8").replace(
                "id: aggregate-classifiers",
                "id: compact-rule",
                1,
            ),
            encoding="utf-8",
        )
        prepared = self.engine.flow_start(str(parent_path))
        analyses = self.engine.flow_next(
            {
                prepared.steps[0].instance_id: {
                    "units": [{"name": "Alpha"}, {"name": "Beta"}]
                },
            }
        )
        self.assertIsNone(analyses.error, analyses.error)
        self.assertEqual(len(analyses.steps), 6)

        exceptions = self.engine.flow_next(
            {
                "Alpha": {
                    "reviews": {
                        "classify_actions": {
                            "actions": [{"name": "load", "is_lifecycle": False}]
                        },
                        "classify_variable_usage": {
                            "method_variable_usage": [
                                {"method": "load", "variables": ["cache"]},
                                {"method": "save", "variables": ["cache"]},
                            ]
                        },
                        "classify_stakeholders": {"stakeholders": ["Operations"]},
                    }
                },
                "Beta": {
                    "reviews": {
                        "classify_actions": {"actions": []},
                        "classify_variable_usage": {"method_variable_usage": []},
                        "classify_stakeholders": {"stakeholders": []},
                    }
                },
            }
        )

        self.assertIsNone(exceptions.error, exceptions.error)
        self.assertEqual(
            [step.step_id for step in exceptions.steps],
            [
                "aggregate_rules.reviews-1.classify_exception",
                "aggregate_rules.reviews-2.classify_exception",
            ],
        )
        metrics = [
            event
            for event in self._events(prepared.run_id)
            if event.get("event") == "step_completed"
            and event.get("session_id") == "engine"
        ]
        self.assertEqual(
            [event["step_id"] for event in metrics],
            [
                "aggregate_rules.reviews-1.action_count",
                "aggregate_rules.reviews-2.action_count",
                "aggregate_rules.reviews-1.cohesion_groups",
                "aggregate_rules.reviews-2.cohesion_groups",
                "aggregate_rules.reviews-1.stakeholder_count",
                "aggregate_rules.reviews-2.stakeholder_count",
            ],
        )
        self.assertEqual(
            [event["outputs"]["value"] for event in metrics], [1, 0, 1, 0, 1, 0]
        )
        self.assertEqual(
            [event["workflow_instance_id"] for event in metrics],
            ["aggregate_rules.reviews-1", "aggregate_rules.reviews-2"] * 3,
        )

    def test_partial_aggregate_scores_only_valid_classifiers_and_retries_missing_work(
        self,
    ) -> None:
        self._write_aggregate_workflow()
        started = self.engine.flow_start(str(self.workflow_path))

        remaining = self.engine.flow_next(
            {
                "aggregate-classifiers": {
                    "aggregate-classifiers": {
                        "classify_actions": {
                            "actions": [
                                {"name": "load", "is_lifecycle": False},
                            ]
                        },
                        "classify_variable_usage": {
                            "method_variable_usage": [
                                {"method": "load", "variables": "not-an-array"},
                            ]
                        },
                    },
                },
            }
        )

        self.assertIsNone(remaining.error, remaining.error)
        self.assertEqual(
            [step.step_id for step in remaining.steps],
            ["classify_variable_usage", "classify_stakeholders"],
        )
        self.assertIn("not of type 'array'", remaining.steps[0].rejection_reason)
        self.assertEqual(
            [
                event["step_id"]
                for event in self._events(started.run_id)
                if event.get("event") == "step_completed"
            ],
            ["classify_actions", "action_count"],
        )
        restarted = self._engine()
        replayed = restarted.flow_next()
        self.assertEqual(
            [step.step_id for step in replayed.steps],
            ["classify_variable_usage", "classify_stakeholders"],
        )

        exception = restarted.flow_next(
            {
                "aggregate-classifiers": {
                    "aggregate-classifiers": {
                        "classify_variable_usage": {
                            "method_variable_usage": [
                                {"method": "load", "variables": ["cache"]},
                            ]
                        },
                        "classify_stakeholders": {"stakeholders": ["Operations"]},
                    },
                },
            }
        )

        self.assertIsNone(exception.error, exception.error)
        self.assertEqual(
            [step.step_id for step in exception.steps], ["classify_exception"]
        )
        self.assertEqual(
            [
                event["step_id"]
                for event in self._events(started.run_id)
                if event.get("event") == "step_completed"
            ],
            [
                "classify_actions",
                "action_count",
                "classify_variable_usage",
                "classify_stakeholders",
                "cohesion_groups",
                "stakeholder_count",
            ],
        )

    def _write_aggregate_workflow(self) -> None:
        fixture = (
            Path(__file__).parent
            / "fixtures/aggregate_co_located_metrics/workflow.yaml"
        )
        self.workflow_path.write_text(
            fixture.read_text(encoding="utf-8"), encoding="utf-8"
        )

    def _engine(self):
        return FlowRunOrchestratorFactory(
            base_dir_resolver=RunsBaseDirResolver(
                project_dir_fn=lambda: self.project_root
            ),
            plugin_root=self.project_root,
        ).build()

    def _metric_events(self, run_id: str) -> list[dict]:
        return [
            event
            for event in self._events(run_id)
            if event.get("event") == "step_completed"
            and event.get("step_id") == "action_count"
        ]

    def _events(self, run_id: str) -> list[dict]:
        events_path = self.project_root / "runs" / run_id / "events.jsonl"
        return [
            json.loads(line)
            for line in events_path.read_text(encoding="utf-8").splitlines()
        ]

    def _write_dynamic_rule_workflows(self) -> Path:
        workflow_root = self.project_root / "workflows" / "review"
        child_path = workflow_root / "compact-rule" / "workflow.yaml"
        child_path.parent.mkdir(parents=True, exist_ok=True)
        child_path.write_text(
            textwrap.dedent(self._workflow()),
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
                      workflow: compact-rule
                    as: reviews
                    depends_on: [prepare]
                    for_each: "{{steps.prepare.outputs.units}}"
                """
            ),
            encoding="utf-8",
        )
        return parent_path

    def _write_combined_dynamic_rule_workflows(self) -> Path:
        parent_path = self._write_dynamic_rule_workflows()
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
                  - group: aggregate_rules
                    execution:
                      mode: aggregate
                    presentation:
                      mode: combined
                    steps:
                      - include:
                          workflow: compact-rule
                        as: reviews
                        depends_on: [prepare]
                        for_each:
                          source: "{{steps.prepare.outputs.units}}"
                          mode: batch
                          label: "{{item.name}}"
                """
            ),
            encoding="utf-8",
        )
        return parent_path

    @staticmethod
    def _workflow() -> str:
        return """
        id: compact-rule
        name: Compact Rule
        max_turns: 5
        rule: {}
        steps:
          - id: classify
            prompt: Classify every action.
            outputs:
              - name: actions
                type: data
                schema:
                  type: array
                  items:
                    type: object
                    additionalProperties: false
                    required: [name, is_lifecycle]
                    properties:
                      name: {type: string}
                      is_lifecycle: {type: boolean}
            metrics:
              - id: action_count
                metric_id: SRP-1
                value: {type: integer, minimum: 0}
                scoring:
                  source: actions
                  when:
                    ref: "{{item.is_lifecycle}}"
                    equals: false
                  severe: {operator: greater_than_or_equal, value: 2}
          - id: classify_exception
            type: exception
            depends_on: [action_count]
            prompt: Classify the whole-rule exception.
        """

    @staticmethod
    def _mixed_workflow() -> str:
        return """
        id: mixed-rule
        name: Mixed Rule
        max_turns: 5
        rule: {}
        steps:
          - id: classify
            prompt: Classify every action.
            outputs:
              - name: actions
                type: data
                schema:
                  type: array
                  items:
                    type: object
                    additionalProperties: false
                    required: [name, is_lifecycle]
                    properties:
                      name: {type: string}
                      is_lifecycle: {type: boolean}
            metrics:
              - id: action_count
                metric_id: SRP-1
                value: {type: integer, minimum: 0}
                scoring:
                  source: actions
                  when:
                    ref: "{{item.is_lifecycle}}"
                    equals: false
                  severe: {operator: greater_than_or_equal, value: 2}
          - id: lifecycle_count
            type: metric
            metric_id: SRP-LIFECYCLE
            depends_on: [classify]
            value: {type: integer, minimum: 0}
            scoring:
              source: "{{steps.classify.outputs.actions}}"
              when:
                ref: "{{item.is_lifecycle}}"
                equals: true
              severe: {operator: greater_than_or_equal, value: 2}
          - id: classify_exception
            type: exception
            depends_on: [action_count, lifecycle_count]
            prompt: Classify the whole-rule exception.
        """


if __name__ == "__main__":
    unittest.main()
