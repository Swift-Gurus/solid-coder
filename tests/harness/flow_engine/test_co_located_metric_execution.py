"""Tests deterministic execution of co-located metrics."""

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
        analyses = engine.flow_next(
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
