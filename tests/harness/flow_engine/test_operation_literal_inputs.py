import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from harness.flow_validation_error import FlowValidationError
from operation_workflow_integration_driver import OperationWorkflowIntegrationDriver


"""
solid-name: TestOperationLiteralInputs
solid-category: integration-test
solid-spec: [SPEC-040, SPEC-057]
solid-description: Verifies fixed operation inputs retain their values alongside runtime references through execution, nesting, and replay.
"""
class TestOperationLiteralInputs(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.driver = OperationWorkflowIntegrationDriver(self.root, [])

    def test_literal_collection_preserves_nested_values_in_saved_workflow(self) -> None:
        self.driver.write_workflow(textwrap.dedent("""
            id: literals
            name: Literals
            max_turns: 5
            steps:
              - id: count
                type: operation
                operation: collection.count
                with:
                  values: [false, null, 2, 2.5, private, {name: reading}]
              - id: report
                depends_on: [count]
                prompt: Count {{steps.count.outputs.value}}.
        """))

        started = self.driver.start()
        resumed = self.driver.advance()

        self.assertIsNone(started.error)
        self.assertEqual(resumed.steps[0].prompt, "Count 6.")
        self.assertEqual(self.completed_operations(started.run_id), ["count"])

    def test_reference_and_literal_inputs_are_both_validated_by_operation(self) -> None:
        self.driver.write_workflow(textwrap.dedent("""
            id: mixed-inputs
            name: Mixed inputs
            max_turns: 5
            steps:
              - id: ratio
                type: operation
                operation: collection.ratio
                with:
                  observations: "{{params.observations}}"
                  empty_value: 0.25
              - id: report
                depends_on: [ratio]
                prompt: Ratio {{steps.ratio.outputs.value}}.
        """))

        started = self.driver.start(params={"observations": []})

        self.assertIsNone(started.error)
        self.assertEqual(started.steps[0].prompt, "Ratio 0.25.")

    def test_nested_operation_retains_literals_after_agent_boundary_and_replay(self) -> None:
        child = self.root / "child.yaml"
        child.write_text(textwrap.dedent("""
            id: child
            name: Child
            max_turns: 5
            steps:
              - id: inspect
                prompt: Inspect.
              - id: count
                type: operation
                operation: collection.count
                depends_on: [inspect]
                with:
                  values: [private, fileprivate]
              - id: report
                depends_on: [count]
                prompt: Count {{steps.count.outputs.value}}.
        """))
        self.driver.write_workflow(textwrap.dedent("""
            id: parent
            name: Parent
            max_turns: 5
            steps:
              - include: ./child.yaml
                as: child
                with:
                  context: "{{params.context}}"
        """))
        started = self.driver.start(params={"context": "nested operation"})
        child.unlink()

        advanced = self.driver.advance({started.steps[0].instance_id: {}})
        resumed = self.driver.advance()

        self.assertIsNone(advanced.error)
        self.assertEqual(advanced.steps[0].prompt, "Count 2.")
        self.assertEqual(resumed.steps[0].prompt, "Count 2.")
        self.assertEqual(self.completed_operations(started.run_id), ["child-1.count"])

    def test_empty_literal_collection_executes_without_model_supplied_parameters(self) -> None:
        self.driver.write_workflow(textwrap.dedent("""
            id: empty
            name: Empty
            max_turns: 5
            steps:
              - id: count
                type: operation
                operation: collection.count
                with:
                  values: []
              - id: report
                depends_on: [count]
                prompt: Count {{steps.count.outputs.value}}.
        """))

        started = self.driver.start()

        self.assertIsNone(started.error)
        self.assertEqual(started.steps[0].prompt, "Count 0.")

    def test_malformed_reference_is_not_silently_treated_as_literal(self) -> None:
        self.driver.write_workflow(textwrap.dedent("""
            id: invalid
            name: Invalid
            max_turns: 5
            steps:
              - id: count
                type: operation
                operation: collection.count
                with:
                  values: "{{params.values}"
        """))

        with self.assertRaisesRegex(FlowValidationError, "incomplete wrapper"):
            self.driver.start()

    def completed_operations(self, run_id: str) -> list[str]:
        events = (self.root / "runs" / run_id / "events.jsonl").read_text().splitlines()
        return [event["step_id"] for line in events
                if (event := json.loads(line))["event"] == "step_completed"
                and event.get("session_id") == "engine"]
