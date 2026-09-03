"""Validates the typed aggregate assessment workflow contract."""

from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.flow_engine_assembly_factory import FlowEngineAssemblyFactory  # noqa: E402
from harness.flow_validation_error import FlowValidationError  # noqa: E402
from harness.workflow_persister_factory import make_workflow_persister  # noqa: E402


"""
solid-name: TestAggregateRuleWorkflowLoading
solid-category: unit-test
solid-spec: [SPEC-044]
solid-description: Verifies aggregate assessment declarations generate audited output contracts and reject ambiguous rule shapes.
"""
class TestAggregateRuleWorkflowLoading(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.loader = FlowEngineAssemblyFactory().build().flow_loader

    def test_loads_typed_assessment_and_generates_audited_outputs(self) -> None:
        flow = self.loader.load(self._write(self._valid_workflow()), [])

        step = flow.steps[0]
        self.assertIsNotNone(step.assessment)
        self.assertEqual(
            [metric.metric_id for metric in step.assessment.metrics],
            ["TEST-1", "TEST-2"],
        )
        self.assertEqual(
            [metric.observation_id for metric in step.assessment.metrics],
            ["count", "blocked"],
        )
        self.assertEqual(step.assessment.exception_observation_id, "exception")
        self.assertEqual(
            [output.name for output in step.outputs],
            ["count", "blocked", "exception"],
        )
        for output in step.outputs:
            self.assertIn("additional_info", output.schema["required"])

    def test_preserves_public_assessment_contract_through_snapshot_reload(self) -> None:
        flow = self.loader.load(self._write(self._workflow_with_supporting_output()), [])
        run_directory = self.directory / "run"
        run_directory.mkdir()

        make_workflow_persister().persist(run_directory, flow)
        snapshot = (run_directory / "workflow.yaml").read_text()
        reloaded = self.loader.load(str(run_directory / "workflow.yaml"), [])

        self.assertIn("assessment:", snapshot)
        self.assertNotIn("\n  outputs:", snapshot)
        self.assertIn("schema:", snapshot)
        self.assertNotIn("schema_value:", snapshot)
        self.assertEqual(reloaded.steps[0].assessment, flow.steps[0].assessment)
        self.assertEqual(reloaded.steps[0].outputs, flow.steps[0].outputs)

    def test_rejects_authored_outputs_on_assessment_step(self) -> None:
        source = self._valid_workflow().replace(
            "    assessment:\n",
            "    outputs:\n"
            "      - name: result\n"
            "        type: data\n"
            "    assessment:\n",
        )

        with self.assertRaisesRegex(FlowValidationError, "must not declare outputs"):
            self.loader.load(self._write(source), [])

    def test_rejects_mixed_aggregate_and_granular_rule_steps(self) -> None:
        source = self._valid_workflow() + (
            "  - id: granular_metric\n"
            "    type: metric\n"
            "    metric_id: TEST-3\n"
            "    prompt: Measure another value.\n"
            "    value: {type: integer}\n"
            "    scoring:\n"
            "      severe: {operator: greater_than, value: 0}\n"
            "  - id: granular_exception\n"
            "    type: exception\n"
            "    prompt: Classify another exception.\n"
        )

        with self.assertRaisesRegex(FlowValidationError, "must not mix"):
            self.loader.load(self._write(source), [])

    def test_rejects_duplicate_metric_observation_ids(self) -> None:
        source = self._valid_workflow().replace(
            "observation_id: blocked",
            "observation_id: count",
        )

        with self.assertRaisesRegex(FlowValidationError, "observation"):
            self.loader.load(self._write(source), [])

    def test_rejects_exception_observation_id_collision(self) -> None:
        source = self._valid_workflow().replace(
            "exception_observation_id: exception",
            "exception_observation_id: count",
        )

        with self.assertRaisesRegex(FlowValidationError, "observation"):
            self.loader.load(self._write(source), [])

    def test_rejects_assessment_without_owning_rule_declaration(self) -> None:
        source = self._valid_workflow().replace("rule: {}\n", "")

        with self.assertRaisesRegex(FlowValidationError, "owning rule declaration"):
            self.loader.load(self._write(source), [])

    def test_generates_declared_supporting_outputs_without_scoring_them(self) -> None:
        flow = self.loader.load(self._write(self._workflow_with_supporting_output()), [])

        self.assertEqual(
            [output.name for output in flow.steps[0].outputs],
            ["analysis", "count", "blocked", "exception"],
        )
        self.assertEqual(
            [metric.metric_id for metric in flow.steps[0].assessment.metrics],
            ["TEST-1", "TEST-2"],
        )

    @classmethod
    def _workflow_with_supporting_output(cls) -> str:
        return cls._valid_workflow().replace(
            "      metrics:\n",
            "      supporting_outputs:\n"
            "        - name: analysis\n"
            "          type: data\n"
            "          schema:\n"
            "            type: array\n"
            "            items: {type: string}\n"
            "      metrics:\n",
        )

    def _write(self, source: str) -> str:
        path = self.directory / "workflow.yaml"
        path.write_text(source, encoding="utf-8")
        return str(path)

    @staticmethod
    def _valid_workflow() -> str:
        return textwrap.dedent(
            """
            id: aggregate-rule
            name: Aggregate Rule
            max_turns: 3
            rule: {}
            steps:
              - id: assess
                prompt: Assess every metric and the exception.
                assessment:
                  metrics:
                    - metric_id: TEST-1
                      observation_id: count
                      value: {type: integer, minimum: 0}
                      scoring:
                        severe: {operator: greater_than, value: 1}
                    - metric_id: TEST-2
                      observation_id: blocked
                      value: {type: boolean}
                      scoring:
                        minor: {operator: equals, value: true}
                  exception_observation_id: exception
            """
        )


if __name__ == "__main__":
    unittest.main()
