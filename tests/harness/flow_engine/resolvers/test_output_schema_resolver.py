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

from harness.flow_validation_error import FlowValidationError
from harness.flow_validation_error_factory import FlowValidationErrorFactory
from harness.output_collection_resolver import OutputCollectionResolver
from harness.output_schema_declaration_validator import OutputSchemaDeclarationValidator
from harness.output_schema_file_loader import OutputSchemaFileLoader
from harness.output_schema_reference_resolver import OutputSchemaReferenceResolver
from harness.output_schema_resolver import OutputSchemaResolver
from harness.path_builder import PathBuilder
from harness.step_declaring_file_resolver import StepDeclaringFileResolver
from harness.workflow_package_root_locator import WorkflowPackageRootLocator
from harness.workflow_resource_path_resolver import WorkflowResourcePathResolver


class StubFileLoader:
    def __init__(self, contents: dict[str, dict]) -> None:
        self._contents = contents

    def load(self, path: Path):
        return self._contents.get(str(path))


def _make_resolver(loader: StubFileLoader) -> OutputSchemaResolver:
    error_factory = FlowValidationErrorFactory()
    resource_path_resolver = WorkflowResourcePathResolver(WorkflowPackageRootLocator())
    reference_resolver = OutputSchemaReferenceResolver(
        declaration_validator=OutputSchemaDeclarationValidator(error_factory),
        schema_loader=OutputSchemaFileLoader(
            loader,
            resource_path_resolver,
            error_factory,
        ),
    )
    return OutputSchemaResolver(
        declaring_file_resolver=StepDeclaringFileResolver(PathBuilder()),
        output_collection_resolver=OutputCollectionResolver(reference_resolver),
    )


class TestOutputSchemaResolver(unittest.TestCase):

    def test_resolves_schema_file_relative_to_flow_file(self):
        flow_path = "/flows/my_flow.yaml"
        schema_path = str(Path("/flows/greeting_schema.json"))
        loader = StubFileLoader({schema_path: {"type": "string"}})
        sut = _make_resolver(loader)
        step = {"id": "step_a", "outputs": [{"name": "greeting", "type": "data", "schema_file": "greeting_schema.json"}]}

        resolved = sut.resolve(step, flow_path)

        self.assertEqual(resolved["outputs"][0]["schema"], {"type": "string"})

    def test_removes_schema_file_key_once_resolved_so_the_output_survives_a_round_trip(self):
        flow_path = "/flows/my_flow.yaml"
        schema_path = str(Path("/flows/greeting_schema.json"))
        loader = StubFileLoader({schema_path: {"type": "string"}})
        sut = _make_resolver(loader)
        step = {"id": "step_a", "outputs": [{"name": "greeting", "type": "data", "schema_file": "greeting_schema.json"}]}

        resolved = sut.resolve(step, flow_path)

        self.assertNotIn("schema_file", resolved["outputs"][0])

    def test_leaves_inline_schema_unchanged_when_no_schema_file(self):
        sut = _make_resolver(StubFileLoader({}))
        step = {"id": "step_a", "outputs": [{"name": "greeting", "type": "data", "schema": {"type": "string"}}]}

        resolved = sut.resolve(step, "/flows/my_flow.yaml")

        self.assertEqual(resolved["outputs"][0]["schema"], {"type": "string"})

    def test_leaves_step_unchanged_when_no_outputs_declared(self):
        sut = _make_resolver(StubFileLoader({}))
        step = {"id": "step_a", "prompt": "p"}

        resolved = sut.resolve(step, "/flows/my_flow.yaml")

        self.assertEqual(resolved, step)

    def test_raises_when_output_declares_both_schema_and_schema_file(self):
        schema_path = str(Path("/flows/greeting_schema.json"))
        loader = StubFileLoader({schema_path: {"type": "string"}})
        sut = _make_resolver(loader)
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
        sut = _make_resolver(StubFileLoader({}))
        step = {"id": "step_a", "outputs": [{"name": "greeting", "type": "data", "schema_file": "missing.json"}]}

        with self.assertRaises(FlowValidationError) as ctx:
            sut.resolve(step, "/flows/my_flow.yaml")

        self.assertIn("step_a", str(ctx.exception))
        self.assertIn("greeting", str(ctx.exception))
        self.assertIn("missing.json", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
