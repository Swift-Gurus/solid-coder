"""
solid-name: test_output_schema_resolver
solid-category: unit-test
solid-spec: [SPEC-027]
solid-description: Tests resolving a step's outputs[].schema_file references into inline outputs[].schema relative to its flow file.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.models import FlowValidationError
from harness.output_schema_resolver import OutputSchemaResolver


class StubFileLoader:
    def __init__(self, contents: dict[str, dict]) -> None:
        self._contents = contents

    def load(self, path: Path):
        return self._contents.get(str(path))


class TestOutputSchemaResolver(unittest.TestCase):

    def test_resolves_schema_file_relative_to_flow_file(self):
        flow_path = "/flows/my_flow.yaml"
        schema_path = str(Path("/flows/greeting_schema.json"))
        loader = StubFileLoader({schema_path: {"type": "string"}})
        sut = OutputSchemaResolver(file_loader=loader)
        step = {"id": "step_a", "outputs": [{"name": "greeting", "type": "data", "schema_file": "greeting_schema.json"}]}

        resolved = sut.resolve(step, flow_path)

        self.assertEqual(resolved["outputs"][0]["schema"], {"type": "string"})

    def test_removes_schema_file_key_once_resolved_so_the_output_survives_a_round_trip(self):
        flow_path = "/flows/my_flow.yaml"
        schema_path = str(Path("/flows/greeting_schema.json"))
        loader = StubFileLoader({schema_path: {"type": "string"}})
        sut = OutputSchemaResolver(file_loader=loader)
        step = {"id": "step_a", "outputs": [{"name": "greeting", "type": "data", "schema_file": "greeting_schema.json"}]}

        resolved = sut.resolve(step, flow_path)

        self.assertNotIn("schema_file", resolved["outputs"][0])

    def test_leaves_inline_schema_unchanged_when_no_schema_file(self):
        sut = OutputSchemaResolver(file_loader=StubFileLoader({}))
        step = {"id": "step_a", "outputs": [{"name": "greeting", "type": "data", "schema": {"type": "string"}}]}

        resolved = sut.resolve(step, "/flows/my_flow.yaml")

        self.assertEqual(resolved["outputs"][0]["schema"], {"type": "string"})

    def test_leaves_step_unchanged_when_no_outputs_declared(self):
        sut = OutputSchemaResolver(file_loader=StubFileLoader({}))
        step = {"id": "step_a", "prompt": "p"}

        resolved = sut.resolve(step, "/flows/my_flow.yaml")

        self.assertEqual(resolved, step)

    def test_raises_when_output_declares_both_schema_and_schema_file(self):
        schema_path = str(Path("/flows/greeting_schema.json"))
        loader = StubFileLoader({schema_path: {"type": "string"}})
        sut = OutputSchemaResolver(file_loader=loader)
        step = {
            "id": "step_a",
            "outputs": [
                {"name": "greeting", "type": "data", "schema": {"type": "integer"}, "schema_file": "greeting_schema.json"}
            ],
        }

        with self.assertRaises(FlowValidationError) as ctx:
            sut.resolve(step, "/flows/my_flow.yaml")

        self.assertIn("step_a", str(ctx.exception))
        self.assertIn("greeting", str(ctx.exception))

    def test_raises_when_schema_file_does_not_resolve(self):
        sut = OutputSchemaResolver(file_loader=StubFileLoader({}))
        step = {"id": "step_a", "outputs": [{"name": "greeting", "type": "data", "schema_file": "missing.json"}]}

        with self.assertRaises(FlowValidationError) as ctx:
            sut.resolve(step, "/flows/my_flow.yaml")

        self.assertIn("step_a", str(ctx.exception))
        self.assertIn("greeting", str(ctx.exception))
        self.assertIn("missing.json", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
