"""Validates compact metric declarations owned by one agent step."""

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.flow_engine_assembly_factory import FlowEngineAssemblyFactory
from harness.step_output_reference import StepOutputReference

"""
solid-name: TestCoLocatedMetricLoading
solid-category: unit-test
solid-spec: [SPEC-058]
solid-description: Verifies compact metrics normalize into existing collection-backed runtime metric steps.
"""


class TestCoLocatedMetricLoading(unittest.TestCase):
    def setUp(self) -> None:
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self.directory = Path(temporary_directory.name)
        self.loader = FlowEngineAssemblyFactory().build().flow_loader

    def test_normalizes_local_output_metric(self) -> None:
        flow = self._load(
            """
            id: compact-metric
            name: Compact Metric
            max_turns: 5
            rule: {}
            steps:
              - id: classify_actions
                type: agent
                prompt: Classify actions.
                outputs:
                  - name: actions
                    type: data
                    schema:
                      type: array
                      items:
                        type: object
                        additionalProperties: false
                        required: [is_lifecycle]
                        properties:
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
                      severe: {operator: greater_than_or_equal, value: 3}
              - id: classify_exception
                type: exception
                depends_on: [action_count]
                prompt: Classify the rule exception.
            """
        )

        self.assertEqual(
            [step.id for step in flow.steps],
            ["classify_actions", "action_count", "classify_exception"],
        )
        producer, metric, _ = flow.steps
        self.assertEqual([output.name for output in producer.outputs], ["actions"])
        self.assertEqual(metric.type, "metric")
        self.assertEqual(metric.depends_on, ["classify_actions"])
        self.assertEqual(metric.metric.metric_id, "SRP-1")
        self.assertEqual(
            metric.metric_calculation.source,
            StepOutputReference(
                step_id="classify_actions",
                output_name="actions",
            ),
        )
        self.assertEqual(
            [output.name for output in metric.outputs],
            ["value", "additional_info"],
        )

    def test_normalizes_multiple_metrics_from_one_output(self) -> None:
        flow = self._load(
            """
            id: compact-metrics
            name: Compact Metrics
            max_turns: 5
            rule: {}
            steps:
              - id: classify
                prompt: Classify observations once.
                outputs:
                  - name: observations
                    type: data
                    schema:
                      type: array
                      items: {type: integer}
                metrics:
                  - id: total
                    metric_id: TEST-1
                    value: {type: integer, minimum: 0}
                    scoring:
                      source: observations
                      severe: {operator: greater_than, value: 1}
                  - id: maximum
                    metric_id: TEST-2
                    value: {type: integer, minimum: 0}
                    scoring:
                      source: observations
                      reducer: {type: maximum, value: "{{item}}"}
                      severe: {operator: greater_than, value: 5}
              - id: classify_exception
                type: exception
                depends_on: [total, maximum]
                prompt: Classify the rule exception.
            """
        )

        self.assertEqual(
            [step.id for step in flow.steps],
            ["classify", "total", "maximum", "classify_exception"],
        )
        self.assertEqual(
            [step.metric.metric_id for step in flow.steps[1:3]],
            ["TEST-1", "TEST-2"],
        )

    def test_preserves_agent_step_without_metrics(self) -> None:
        flow = self._load(
            """
            id: no-compact-metric
            name: No Compact Metric
            max_turns: 2
            steps:
              - id: prepare
                prompt: Prepare context.
                outputs:
                  - name: context
                    type: string
            """
        )

        self.assertEqual([step.id for step in flow.steps], ["prepare"])
        self.assertEqual(flow.steps[0].type, "agent")

    def _load(self, source: str):
        path = self.directory / "workflow.yaml"
        path.write_text(textwrap.dedent(source), encoding="utf-8")
        return self.loader.load(str(path), [])
