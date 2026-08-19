"""
solid-name: test_operation_step_execution
solid-category: integration-test
solid-spec: [SPEC-010, SPEC-040]
solid-description: Defines the required internal logical-operation workflow contract before its implementation.
"""

from __future__ import annotations

import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from pydantic import BaseModel, ConfigDict

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from harness.flow_validation_error import FlowValidationError
from harness.operation_registration import OperationRegistration
from operation_workflow_integration_driver import OperationWorkflowIntegrationDriver


class EchoInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    value: str


class EchoOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    echoed: str


class EchoOperation:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, operation_input: EchoInput) -> EchoOutput:
        self.calls += 1
        return EchoOutput(echoed=operation_input.value)


class TestOperationStepExecution(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project_root = Path(temporary.name)
        self.runs_dir = self.project_root / "runs"
        self.workflow_path = self.project_root / "workflow.yaml"
        self.operation = EchoOperation()
        self.registration = OperationRegistration(
            name="test.echo",
            input_model=EchoInput,
            output_model=EchoOutput,
            handler=self.operation,
        )
        self.driver = OperationWorkflowIntegrationDriver(
            project_root=self.project_root,
            registrations=[self.registration],
        )

    def test_executes_logical_operation_inside_engine_before_returning_agent_work(self) -> None:
        self._write_workflow("test.echo")

        started = self.driver.start(params={"message": "hello"})

        self.assertIsNone(started.error, started.error)
        self.assertEqual([step.step_id for step in started.steps], ["report"])
        self.assertEqual(started.steps[0].prompt, "Report hello.")
        completed = self._completed_events(started.run_id)
        operation_event = next(
            event for event in completed if event["step_id"] == "echo"
        )
        self.assertEqual(operation_event["session_id"], "engine")
        self.assertEqual(operation_event["outputs"], {"echoed": "hello"})

    def test_replay_uses_persisted_output_without_invoking_operation_again(self) -> None:
        self._write_workflow("test.echo")
        started = self.driver.start(params={"message": "hello"})
        self.assertEqual(self.operation.calls, 1)

        resumed = self.driver.advance(
            {started.steps[0].instance_id: {}}
        )

        self.assertEqual(resumed.status, "done")
        self.assertEqual(self.operation.calls, 1)

    def test_for_each_executes_every_operation_and_aggregates_in_source_order(self) -> None:
        self.driver.write_workflow(
            textwrap.dedent(
                """
                name: operation-for-each-test
                max_turns: 10
                steps:
                  - id: prepare
                    prompt: Prepare messages.
                    outputs:
                      - name: messages
                        type: data
                        schema:
                          type: array
                          items:
                            type: string
                  - id: echo
                    type: operation
                    operation: test.echo
                    depends_on: [prepare]
                    for_each: "{{steps.prepare.outputs.messages}}"
                    with:
                      value: "{{item}}"
                  - id: report
                    depends_on: [echo]
                    prompt: Report {{steps.echo.outputs.echoed}}.
                """
            )
        )

        started = self.driver.start()
        result = self.driver.advance(
            {
                started.steps[0].instance_id: {
                    "messages": ["first", "second", "third"]
                }
            }
        )

        self.assertEqual(self.operation.calls, 3)
        self.assertEqual([step.step_id for step in result.steps], ["report"])
        self.assertIn("first", result.steps[0].prompt)
        self.assertIn("second", result.steps[0].prompt)
        self.assertIn("third", result.steps[0].prompt)

    def test_rejects_unknown_logical_operation_before_execution(self) -> None:
        self._write_workflow("source.missing")

        with self.assertRaisesRegex(FlowValidationError, "source.missing"):
            self.driver.start(params={"message": "hello"})

    def test_rejects_transport_qualified_mcp_tool_name(self) -> None:
        self._write_workflow("mcp__plugin_solid-coder_source__analyze")

        with self.assertRaisesRegex(FlowValidationError, "logical operation"):
            self.driver.start(params={"message": "hello"})

    def _write_workflow(self, operation: str) -> None:
        self.driver.write_workflow(
            textwrap.dedent(
                f"""
                name: operation-test
                max_turns: 5
                steps:
                  - id: echo
                    type: operation
                    operation: {operation}
                    with:
                      value: "{{{{params.message}}}}"
                  - id: report
                    depends_on: [echo]
                    prompt: Report {{{{steps.echo.outputs.echoed}}}}.
                """
            )
        )

    def _completed_events(self, run_id: str) -> list[dict]:
        events_path = self.runs_dir / run_id / "events.jsonl"
        return [
            json.loads(line)
            for line in events_path.read_text(encoding="utf-8").splitlines()
            if json.loads(line).get("event") == "step_completed"
        ]


if __name__ == "__main__":
    unittest.main()
