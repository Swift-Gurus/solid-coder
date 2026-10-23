"""Tests intermediate collection counting composed with metric reducers."""

import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from harness.flow_run_orchestrator_factory import (
    FlowRunOrchestratorFactory,
)
from harness.runs_base_dir_resolver import RunsBaseDirResolver

"""
solid-name: TestCollectionCountReducerComposition
solid-category: integration-test
solid-spec: [SPEC-057]
solid-description: Verifies operation fan-out counts nested evidence before an engine-owned maximum metric.
"""


class TestCollectionCountReducerComposition(unittest.TestCase):
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

    def test_counts_nested_collections_before_selecting_the_maximum(self) -> None:
        started = self.engine.flow_start(str(self.workflow_path))

        exception = self.engine.flow_next(
            {
                started.steps[0].instance_id: {
                    "groups": [
                        {
                            "values": ["VStack", "HStack", "Text"],
                            "is_exception": False,
                        },
                        {
                            "values": ["Preview", "Only", "Content", "Text"],
                            "is_exception": True,
                        },
                        {
                            "values": ["HStack", "Text"],
                            "is_exception": False,
                        },
                    ]
                }
            }
        )

        self.assertIsNone(exception.error, exception.error)
        self.assertEqual(
            [step.step_id for step in exception.steps],
            ["classify_exception"],
        )
        events = self._events(started.run_id)
        count_events = [
            event
            for event in events
            if event.get("step_id") == "count_values"
            and event.get("event") == "step_completed"
        ]
        self.assertEqual(
            [event["outputs"]["value"] for event in count_events],
            [3, 2],
        )
        metric_event = next(
            event
            for event in events
            if event.get("step_id") == "maximum_count"
            and event.get("event") == "step_completed"
        )
        self.assertEqual(metric_event["outputs"]["value"], 3)
        self.assertEqual(
            metric_event["metric_derivation"]["projection_evidence"],
            [{"index": 0, "value": 3}, {"index": 1, "value": 2}],
        )

    def test_uses_zero_when_every_nested_collection_is_excluded(self) -> None:
        started = self.engine.flow_start(str(self.workflow_path))

        exception = self.engine.flow_next(
            {
                started.steps[0].instance_id: {
                    "groups": [
                        {
                            "values": ["Preview", "Only", "Content"],
                            "is_exception": True,
                        },
                    ]
                }
            }
        )

        self.assertIsNone(exception.error, exception.error)
        self.assertEqual(
            [step.step_id for step in exception.steps],
            ["classify_exception"],
        )
        metric_event = next(
            event
            for event in self._events(started.run_id)
            if event.get("step_id") == "maximum_count"
            and event.get("event") == "step_completed"
        )
        self.assertEqual(metric_event["outputs"]["value"], 0)
        self.assertEqual(
            metric_event["metric_derivation"]["projection_evidence"],
            [],
        )

    def _events(self, run_id: str) -> list[dict]:
        events_path = self.project_root / "runs" / run_id / "events.jsonl"
        return [
            json.loads(line)
            for line in events_path.read_text(encoding="utf-8").splitlines()
        ]

    @staticmethod
    def _workflow() -> str:
        return """
        id: nested-collection-review
        name: Nested Collection Review
        max_turns: 5
        rule: {}
        steps:
          - id: classify_groups
            prompt: Return complete evidence groups.
            outputs:
              - name: groups
                type: data
                schema:
                  type: array
                  items:
                    type: object
                    additionalProperties: false
                    required: [values, is_exception]
                    properties:
                      values:
                        type: array
                        items: {type: string}
                      is_exception: {type: boolean}

          - id: count_values
            type: operation
            operation: collection.count
            depends_on: [classify_groups]
            for_each: "{{steps.classify_groups.outputs.groups}}"
            when:
              ref: "{{item.is_exception}}"
              equals: false
            with:
              values: "{{item.values}}"

          - id: maximum_count
            type: metric
            metric_id: TEST-1
            depends_on: [count_values]
            value: {type: integer, minimum: 0}
            scoring:
              source: "{{steps.count_values.outputs.value}}"
              reducer:
                type: maximum
                value: "{{item}}"
                empty_value: 0
              severe: {operator: greater_than_or_equal, value: 3}

          - id: classify_exception
            type: exception
            depends_on: [maximum_count]
            prompt: Classify the whole-rule exception.
        """


if __name__ == "__main__":
    unittest.main()
