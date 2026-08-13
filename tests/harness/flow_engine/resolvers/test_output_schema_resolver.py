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
from harness.output_spec import OutputSpec
from harness.output_spec_factory import OutputSpecFactory
from harness.output_schema_declaration_validator import OutputSchemaDeclarationValidator
from harness.output_schema_file_loader import OutputSchemaFileLoader
from harness.output_schema_reference_resolver import OutputSchemaReferenceResolver
from harness.output_schema_resolver import OutputSchemaResolver
from harness.path_builder import PathBuilder
from harness.resolved_output_schema_applier import ResolvedOutputSchemaApplier
from harness.resolved_outputs_applier import ResolvedOutputsApplier
from harness.resolved_step_resources_applier import ResolvedStepResourcesApplier
from harness.resolved_step_resources_factory import ResolvedStepResourcesFactory
from harness.step_declaring_file_resolver import StepDeclaringFileResolver
from harness.step_declaration import StepDeclaration
from harness.step_identity_resolver import StepIdentityResolver
from harness.workflow_config_resource_loader import WorkflowConfigResourceLoader
from harness.workflow_package_root_locator import WorkflowPackageRootLocator
from harness.workflow_resource_directory import WorkflowResourceDirectory
from harness.workflow_resource_path_classifier import WorkflowResourcePathClassifier
from harness.workflow_resource_path_resolver import WorkflowResourcePathResolver
from harness.workflow_resource_reference_factory import WorkflowResourceReferenceFactory


class StubFileLoader:
    def __init__(self, contents: dict[str, dict]) -> None:
        self._contents = contents

    def load(self, path: Path):
        return self._contents.get(str(path))


def _make_resolver(loader: StubFileLoader) -> OutputSchemaResolver:
    error_factory = FlowValidationErrorFactory()
    resource_path_resolver = WorkflowResourcePathResolver(
        WorkflowPackageRootLocator(),
        error_factory,
    )
    reference_factory = WorkflowResourceReferenceFactory(
        WorkflowResourcePathClassifier(),
        WorkflowResourceDirectory.SCHEMAS,
    )
    reference_resolver = OutputSchemaReferenceResolver(
        declaration_validator=OutputSchemaDeclarationValidator(error_factory),
        schema_loader=OutputSchemaFileLoader(
            WorkflowConfigResourceLoader(loader, resource_path_resolver),
            reference_factory,
            error_factory,
        ),
        schema_applier=ResolvedOutputSchemaApplier(OutputSpecFactory()),
        identity_resolver=StepIdentityResolver(error_factory),
    )
    resources_factory = ResolvedStepResourcesFactory()
    return OutputSchemaResolver(
        declaring_file_resolver=StepDeclaringFileResolver(PathBuilder()),
        output_collection_resolver=OutputCollectionResolver(reference_resolver),
        outputs_applier=ResolvedOutputsApplier(
            resources_factory,
            ResolvedStepResourcesApplier(),
        ),
    )


class TestOutputSchemaResolver(unittest.TestCase):

    def test_resolves_schema_file_relative_to_flow_file(self):
        flow_path = "/flows/my_flow.yaml"
        schema_path = str(Path("/flows/greeting_schema.json"))
        loader = StubFileLoader({schema_path: {"type": "string"}})
        sut = _make_resolver(loader)
        step = StepDeclaration(
            id="step_a",
            outputs=[
                OutputSpec(
                    name="greeting",
                    type="data",
                    schema_file="greeting_schema.json",
                )
            ],
        )

        resolved = sut.resolve(step, flow_path)

        self.assertEqual(resolved.outputs[0].schema, {"type": "string"})

    def test_removes_schema_file_key_once_resolved_so_the_output_survives_a_round_trip(self):
        flow_path = "/flows/my_flow.yaml"
        schema_path = str(Path("/flows/greeting_schema.json"))
        loader = StubFileLoader({schema_path: {"type": "string"}})
        sut = _make_resolver(loader)
        step = StepDeclaration(
            id="step_a",
            outputs=[
                OutputSpec(
                    name="greeting",
                    type="data",
                    schema_file="greeting_schema.json",
                )
            ],
        )

        resolved = sut.resolve(step, flow_path)

        self.assertIsNone(resolved.outputs[0].schema_file)

    def test_leaves_inline_schema_unchanged_when_no_schema_file(self):
        sut = _make_resolver(StubFileLoader({}))
        step = StepDeclaration(
            id="step_a",
            outputs=[
                OutputSpec(
                    name="greeting",
                    type="data",
                    schema={"type": "string"},
                )
            ],
        )

        resolved = sut.resolve(step, "/flows/my_flow.yaml")

        self.assertEqual(resolved.outputs[0].schema, {"type": "string"})

    def test_leaves_step_unchanged_when_no_outputs_declared(self):
        sut = _make_resolver(StubFileLoader({}))
        step = StepDeclaration(id="step_a", prompt="p")

        resolved = sut.resolve(step, "/flows/my_flow.yaml")

        self.assertEqual(resolved, step)

    def test_raises_when_output_declares_both_schema_and_schema_file(self):
        schema_path = str(Path("/flows/greeting_schema.json"))
        loader = StubFileLoader({schema_path: {"type": "string"}})
        sut = _make_resolver(loader)
        step = StepDeclaration(
            id="step_a",
            outputs=[
                OutputSpec(
                    name="greeting",
                    type="data",
                    schema={"type": "integer"},
                    schema_file="greeting_schema.json",
                )
            ],
        )

        with self.assertRaises(FlowValidationError) as ctx:
            sut.resolve(step, "/flows/my_flow.yaml")

        self.assertIn("step_a", str(ctx.exception))
        self.assertIn("greeting", str(ctx.exception))

    def test_raises_when_schema_file_does_not_resolve(self):
        sut = _make_resolver(StubFileLoader({}))
        step = StepDeclaration(
            id="step_a",
            outputs=[
                OutputSpec(
                    name="greeting",
                    type="data",
                    schema_file="missing.json",
                )
            ],
        )

        with self.assertRaises(FlowValidationError) as ctx:
            sut.resolve(step, "/flows/my_flow.yaml")

        self.assertIn("step_a", str(ctx.exception))
        self.assertIn("greeting", str(ctx.exception))
        self.assertIn("missing.json", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
