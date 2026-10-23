"""Exercises pairwise grouping, audit, and replay through the public engine."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from harness.flow_run_orchestrator_factory import FlowRunOrchestratorFactory
from harness.project_context import ProjectDirectory
from harness.runs_base_dir_resolver import RunsBaseDirResolver

"""
solid-name: TestComponentMetricExecution
solid-category: integration-test
solid-spec: [SPEC-059]
solid-description: Verifies filtered set grouping is engine-owned and durably replayed with component evidence.
"""


class TestComponentMetricExecution(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.path = self.root / "workflow.yaml"
        self.path.write_text(
            (
                Path(__file__).parent / "fixtures/component_count/workflow.yaml"
            ).read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        self.engine = self._engine()

    def test_filters_bridge_then_preserves_transitive_groups_through_replay(
        self,
    ) -> None:
        started = self.engine.flow_start(str(self.path))
        self.assertIsNone(started.error, started.error)
        advanced = self.engine.flow_next(
            {
                started.steps[0].instance_id: {
                    "items": [
                        {"name": "A", "resources": ["cache"], "excluded": False},
                        {
                            "name": "B",
                            "resources": ["cache", "storage"],
                            "excluded": False,
                        },
                        {"name": "C", "resources": ["storage"], "excluded": False},
                        {"name": "D", "resources": ["formatter"], "excluded": False},
                        {
                            "name": "E",
                            "resources": ["storage", "formatter"],
                            "excluded": True,
                        },
                    ]
                }
            }
        )
        self.assertIsNone(advanced.error, advanced.error)
        self.assertEqual(
            [step.step_id for step in advanced.steps], ["classify_exception"]
        )
        event = self._metric_event(started.run_id)
        self.assertEqual(event["session_id"], "engine")
        self.assertEqual(event["outputs"]["value"], 2)
        audit = event["metric_derivation"]["component_evidence"]
        self.assertEqual(audit["components"], [[0, 1, 2], [3]])
        self.assertEqual(
            audit["edges"],
            [{"left_index": 0, "right_index": 1}, {"left_index": 1, "right_index": 2}],
        )
        self.assertEqual(event["metric_derivation"]["excluded_indexes"], [4])
        self.assertEqual(audit["projections"][1]["left"], ["cache", "storage"])
        replayed = self._engine().flow_next()
        self.assertIsNone(replayed.error, replayed.error)
        self.assertEqual(self._metric_event(started.run_id), event)
        self.assertEqual(
            sum(
                e.get("step_id") == "groups" and e["event"] == "step_completed"
                for e in self._events(started.run_id)
            ),
            1,
        )
        completed = self.engine.flow_next(
            {
                advanced.steps[0].instance_id: {
                    "is_exception": False,
                    "additional_info": {
                        "reasoning": "No exemption.",
                        "evidence": "Two resource groups.",
                    },
                }
            }
        )
        self.assertEqual(completed.status, "done")
        result_path = (
            self.root
            / "runs"
            / started.run_id
            / "results/review/component-count-contract"
            / started.run_id
            / "result.json"
        )
        result = json.loads(result_path.read_text())
        self.assertEqual(result["metrics"][0]["severity"], "SEVERE")
        self.assertEqual(
            result["metrics"][0]["derivation"]["component_evidence"], audit
        )

    def test_empty_sets_remain_isolated_and_duplicate_members_do_not_change_groups(
        self,
    ) -> None:
        started = self.engine.flow_start(str(self.path))
        self.assertIsNone(started.error, started.error)
        self.engine.flow_next(
            {
                started.steps[0].instance_id: {
                    "items": [
                        {"name": "same", "resources": [], "excluded": False},
                        {"name": "same", "resources": [], "excluded": False},
                        {"name": "same", "resources": ["a", "a"], "excluded": False},
                        {"name": "same", "resources": ["a"], "excluded": False},
                    ]
                }
            }
        )
        event = self._metric_event(started.run_id)
        self.assertEqual(event["outputs"]["value"], 3)
        self.assertEqual(
            event["metric_derivation"]["component_evidence"]["components"],
            [[0], [1], [2, 3]],
        )

    def test_empty_collection_derives_zero(self) -> None:
        started = self.engine.flow_start(str(self.path))
        self.assertIsNone(started.error, started.error)
        self.engine.flow_next({started.steps[0].instance_id: {"items": []}})
        event = self._metric_event(started.run_id)
        self.assertEqual(event["outputs"]["value"], 0)
        self.assertEqual(
            event["metric_derivation"]["component_evidence"]["components"], []
        )

    def test_rejects_wrong_schema_then_accepts_corrected_submission(self) -> None:
        started = self.engine.flow_start(str(self.path))
        self.assertIsNone(started.error, started.error)
        rejected = self.engine.flow_next(
            {
                started.steps[0].instance_id: {
                    "items": [
                        {"name": "A", "resources": "cache", "excluded": False},
                    ]
                }
            }
        )
        self.assertTrue(rejected.steps[0].rejection_reason)
        self.assertFalse(
            any(e.get("step_id") == "groups" for e in self._events(started.run_id))
        )
        corrected = self.engine.flow_next(
            {
                started.steps[0].instance_id: {
                    "items": [
                        {"name": "A", "resources": ["cache"], "excluded": False},
                    ]
                }
            }
        )
        self.assertIsNone(corrected.error, corrected.error)
        self.assertEqual(self._metric_event(started.run_id)["outputs"]["value"], 1)

    def _engine(self):
        return FlowRunOrchestratorFactory(
            base_dir_resolver=RunsBaseDirResolver(project_dir_fn=lambda: self.root),
            plugin_root=self.root,
            project_directory=ProjectDirectory(path=self.root),
        ).build()

    def test_explicit_metric_form_uses_the_same_component_runtime(self) -> None:
        document = yaml.safe_load(self.path.read_text())
        metric = document["steps"][0].pop("metrics")[0]
        metric["type"] = "metric"
        metric["depends_on"] = ["classify"]
        metric["scoring"]["source"] = "{{steps.classify.outputs.items}}"
        document["steps"].insert(1, metric)
        self.path.write_text(yaml.safe_dump(document))

        started = self.engine.flow_start(str(self.path))
        advanced = self.engine.flow_next(
            {
                started.steps[0].instance_id: {
                    "items": [
                        {"name": "A", "resources": ["a"], "excluded": False},
                        {"name": "B", "resources": ["a"], "excluded": False},
                    ]
                }
            }
        )

        self.assertIsNone(advanced.error, advanced.error)
        self.assertEqual(self._metric_event(started.run_id)["outputs"]["value"], 1)

    def test_srp_shaped_facts_filter_lifecycle_and_orchestrator_methods(self) -> None:
        document = yaml.safe_load(self.path.read_text())
        analysis = document["steps"][0]
        output = analysis["outputs"][0]
        output["name"] = "method_variable_usage"
        output["schema"]["items"] = {
            "type": "object",
            "additionalProperties": False,
            "required": ["method", "variables", "is_lifecycle", "is_orchestrator"],
            "properties": {
                "method": {"type": "string"},
                "variables": {"type": "array", "items": {"type": "string"}},
                "is_lifecycle": {"type": "boolean"},
                "is_orchestrator": {"type": "boolean"},
            },
        }
        metric = analysis["metrics"][0]
        metric["metric_id"] = "SRP-2"
        metric["scoring"]["source"] = "method_variable_usage"
        metric["scoring"]["when"] = {
            "all": [
                {"ref": "{{item.is_lifecycle}}", "equals": False},
                {"ref": "{{item.is_orchestrator}}", "equals": False},
            ]
        }
        metric["scoring"]["reducer"]["relation"] = {
            "operator": "intersects",
            "left": "{{left.variables}}",
            "right": "{{right.variables}}",
        }
        self.path.write_text(yaml.safe_dump(document))

        started = self.engine.flow_start(str(self.path))
        advanced = self.engine.flow_next(
            {
                started.steps[0].instance_id: {
                    "method_variable_usage": [
                        {
                            "method": "init",
                            "variables": ["cache", "view"],
                            "is_lifecycle": True,
                            "is_orchestrator": False,
                        },
                        {
                            "method": "coordinate",
                            "variables": ["cache", "view"],
                            "is_lifecycle": False,
                            "is_orchestrator": True,
                        },
                        {
                            "method": "load",
                            "variables": ["cache"],
                            "is_lifecycle": False,
                            "is_orchestrator": False,
                        },
                        {
                            "method": "save",
                            "variables": ["cache", "storage"],
                            "is_lifecycle": False,
                            "is_orchestrator": False,
                        },
                        {
                            "method": "render",
                            "variables": ["view"],
                            "is_lifecycle": False,
                            "is_orchestrator": False,
                        },
                    ]
                }
            }
        )

        self.assertIsNone(advanced.error, advanced.error)
        event = self._metric_event(started.run_id)
        self.assertEqual(event["outputs"]["value"], 2)
        self.assertEqual(event["metric_derivation"]["excluded_indexes"], [0, 1])
        self.assertEqual(
            event["metric_derivation"]["component_evidence"]["components"],
            [[2, 3], [4]],
        )

    def test_project_band_override_scores_the_component_count(self) -> None:
        policy = self.root / ".solid-coder/policies/review.yaml"
        policy.parent.mkdir(parents=True)
        policy.write_text(
            yaml.safe_dump(
                {
                    "version": 1,
                    "rules": [
                        {
                            "workflow_id": "component-count-contract",
                            "metrics": [
                                {
                                    "id": "RESOURCE-GROUPS",
                                    "reason": "Allow two groups.",
                                    "scoring": {
                                        "severe": {
                                            "operator": "greater_than_or_equal",
                                            "value": 3,
                                        }
                                    },
                                }
                            ],
                        }
                    ],
                }
            )
        )

        started = self.engine.flow_start(str(self.path))
        advanced = self.engine.flow_next(
            {
                started.steps[0].instance_id: {
                    "items": [
                        {"name": "A", "resources": ["a"], "excluded": False},
                        {"name": "B", "resources": ["b"], "excluded": False},
                    ]
                }
            }
        )
        completed = self.engine.flow_next(
            {
                advanced.steps[0].instance_id: {
                    "is_exception": False,
                    "additional_info": {
                        "reasoning": "No exemption.",
                        "evidence": "Two distinct resource groups.",
                    },
                }
            }
        )
        result_path = (
            self.root
            / "runs"
            / started.run_id
            / "results/review/component-count-contract"
            / started.run_id
            / "result.json"
        )
        result = json.loads(result_path.read_text())

        self.assertEqual(completed.status, "done", completed.error)
        self.assertEqual(result["metrics"][0]["value"], 2)
        self.assertEqual(result["metrics"][0]["severity"], "COMPLIANT")

    def test_nested_aggregate_keeps_component_audits_scoped_to_each_child(self) -> None:
        child = self.root / "workflows/review/groups/workflow.yaml"
        child.parent.mkdir(parents=True)
        child.write_text(self.path.read_text())
        self.path.write_text(
            yaml.safe_dump(
                {
                    "id": "parent",
                    "name": "Nested Components",
                    "max_turns": 10,
                    "steps": [
                        {
                            "id": "prepare",
                            "prompt": "Classify targets.",
                            "outputs": [
                                {
                                    "name": "targets",
                                    "type": "data",
                                    "schema": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "required": ["name"],
                                            "properties": {"name": {"type": "string"}},
                                        },
                                    },
                                }
                            ],
                        },
                        {
                            "group": "aggregate",
                            "execution": {"mode": "aggregate"},
                            "presentation": {"mode": "combined"},
                            "steps": [
                                {
                                    "include": {"workflow": "component-count-contract"},
                                    "as": "reviews",
                                    "depends_on": ["prepare"],
                                    "for_each": {
                                        "source": "{{steps.prepare.outputs.targets}}",
                                        "mode": "batch",
                                        "label": "{{item.name}}",
                                    },
                                }
                            ],
                        },
                    ],
                }
            )
        )

        started = self.engine.flow_start(str(self.path))
        analyses = self.engine.flow_next(
            {
                started.steps[0].instance_id: {
                    "targets": [{"name": "Alpha"}, {"name": "Beta"}]
                }
            }
        )
        exceptions = self.engine.flow_next(
            {
                "Alpha": {
                    "reviews": {
                        "classify": {
                            "items": [{"name": "a", "resources": [], "excluded": False}]
                        }
                    }
                },
                "Beta": {
                    "reviews": {
                        "classify": {
                            "items": [
                                {"name": "a", "resources": ["a"], "excluded": False},
                                {"name": "b", "resources": ["b"], "excluded": False},
                            ]
                        }
                    }
                },
            }
        )
        events = [
            event
            for event in self._events(started.run_id)
            if event["event"] == "step_completed"
            and event.get("session_id") == "engine"
        ]

        self.assertIsNone(analyses.error, analyses.error)
        self.assertIsNone(exceptions.error, exceptions.error)
        self.assertEqual([event["outputs"]["value"] for event in events], [1, 2])
        self.assertEqual(
            [
                event["metric_derivation"]["component_evidence"]["components"]
                for event in events
            ],
            [[[0]], [[0], [1]]],
        )
        self.assertEqual(
            [event["workflow_instance_id"] for event in events],
            ["aggregate.reviews-1", "aggregate.reviews-2"],
        )

    def _events(self, run_id: str) -> list[dict]:
        path = self.root / "runs" / run_id / "events.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines()]

    def test_projected_child_workflow_output_supports_component_scoring(self) -> None:
        document = yaml.safe_load(self.path.read_text())
        analysis = document["steps"][0]
        item_schema = analysis["outputs"][0]["schema"]["items"]
        metric = analysis["metrics"][0]
        metric["type"] = "metric"
        metric["depends_on"] = ["analyses"]
        metric["scoring"]["source"] = "{{workflows.analyses.outputs.assessment}}"
        child = self.root / "child.yaml"
        child.write_text(
            yaml.safe_dump(
                {
                    "id": "child-analysis",
                    "name": "Child Analysis",
                    "outputs": [
                        {
                            "name": "assessment",
                            "type": "data",
                            "value": "{{steps.analyze.outputs.assessment}}",
                            "schema": item_schema,
                        }
                    ],
                    "steps": [
                        {
                            "id": "analyze",
                            "prompt": "Classify resource usage.",
                            "outputs": [
                                {
                                    "name": "assessment",
                                    "type": "data",
                                    "schema": item_schema,
                                }
                            ],
                        }
                    ],
                }
            )
        )
        document["steps"] = [
            {"include": "./child.yaml", "as": "analyses"},
            metric,
            document["steps"][1],
        ]
        self.path.write_text(yaml.safe_dump(document))

        started = self.engine.flow_start(str(self.path))
        advanced = self.engine.flow_next(
            {
                started.steps[0].instance_id: {
                    "assessment": {
                        "name": "A",
                        "resources": ["cache"],
                        "excluded": False,
                    }
                }
            }
        )
        event = self._metric_event(started.run_id)

        self.assertIsNone(advanced.error, advanced.error)
        self.assertEqual(event["outputs"]["value"], 1)
        self.assertEqual(
            event["metric_derivation"]["source"],
            {
                "kind": "workflow_output",
                "workflow_alias": "analyses",
                "output_name": "assessment",
            },
        )
        self.assertEqual(
            event["metric_derivation"]["component_evidence"]["components"], [[0]]
        )

    def test_resume_derives_a_pending_component_metric_exactly_once(self) -> None:
        started = self.engine.flow_start(str(self.path))
        self.engine.flow_next(
            {
                started.steps[0].instance_id: {
                    "items": [
                        {"name": "A", "resources": ["a"], "excluded": False},
                    ]
                }
            }
        )
        events_path = self.root / "runs" / started.run_id / "events.jsonl"
        retained = [
            event
            for event in self._events(started.run_id)
            if event.get("step_id") != "groups"
            and event.get("instance_id") != "groups-1"
        ]
        events_path.write_text("".join(json.dumps(event) + "\n" for event in retained))

        resumed = self._engine().flow_next()
        replayed = self._engine().flow_next()
        completed_metrics = [
            event
            for event in self._events(started.run_id)
            if event["event"] == "step_completed" and event.get("step_id") == "groups"
        ]

        self.assertIsNone(resumed.error, resumed.error)
        self.assertIsNone(replayed.error, replayed.error)
        self.assertEqual(len(completed_metrics), 1)
        self.assertEqual(completed_metrics[0]["outputs"]["value"], 1)

    def test_whole_rule_exception_preserves_raw_component_audit(self) -> None:
        started = self.engine.flow_start(str(self.path))
        advanced = self.engine.flow_next(
            {
                started.steps[0].instance_id: {
                    "items": [
                        {"name": "A", "resources": ["a"], "excluded": False},
                        {"name": "B", "resources": ["b"], "excluded": False},
                    ]
                }
            }
        )
        completed = self.engine.flow_next(
            {
                advanced.steps[0].instance_id: {
                    "is_exception": True,
                    "additional_info": {
                        "reasoning": "The supplied rule exemption applies.",
                        "evidence": "Fixture is exempt without discarding its measured resource groups.",
                    },
                }
            }
        )
        result_path = (
            self.root
            / "runs"
            / started.run_id
            / "results/review/component-count-contract"
            / started.run_id
            / "result.json"
        )
        result = json.loads(result_path.read_text())

        self.assertEqual(completed.status, "done", completed.error)
        self.assertEqual(result["severity"], "COMPLIANT")
        self.assertEqual(result["metrics"][0]["value"], 2)
        self.assertEqual(
            result["metrics"][0]["derivation"]["component_evidence"]["components"],
            [[0], [1]],
        )

    def _metric_event(self, run_id: str) -> dict:
        return next(
            e
            for e in self._events(run_id)
            if e["event"] == "step_completed" and e.get("step_id") == "groups"
        )
