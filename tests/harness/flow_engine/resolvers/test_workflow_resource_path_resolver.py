"""
solid-name: test_workflow_resource_path_resolver
solid-category: unit-test
solid-spec: [SPEC-035]
solid-description: Tests enum-backed workflow resource classification, anchoring, legacy fallback, and package containment.
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.flow_validation_error import FlowValidationError
from harness.flow_validation_error_factory import FlowValidationErrorFactory
from harness.workflow_package_root_locator import WorkflowPackageRootLocator
from harness.workflow_resource_directory import WorkflowResourceDirectory
from harness.workflow_resource_path_classifier import WorkflowResourcePathClassifier
from harness.workflow_resource_path_resolver import WorkflowResourcePathResolver
from harness.workflow_resource_reference_factory import WorkflowResourceReferenceFactory
from harness.workflow_resource_reference_kind import WorkflowResourceReferenceKind


class TestWorkflowResourcePathResolver(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name).resolve()
        self.package = self.root / "review"
        self.package.mkdir()
        self.workflow = self.package / "workflow.yaml"
        self.workflow.write_text("id: review\n")
        self.reference_factory = WorkflowResourceReferenceFactory(
            WorkflowResourcePathClassifier(),
            WorkflowResourceDirectory.PROMPTS,
        )
        self.sut = WorkflowResourcePathResolver(
            WorkflowPackageRootLocator(),
            FlowValidationErrorFactory(),
        )

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_factory_classifies_package_reference_before_resolution(self):
        reference = self.reference_factory.create("$package/custom/review.md")

        self.assertEqual(reference.kind, WorkflowResourceReferenceKind.PACKAGE_ROOT)
        self.assertEqual(reference.path, Path("custom/review.md"))

    def test_factory_classifies_bare_reference_with_conventional_directory(self):
        reference = self.reference_factory.create("review.md")

        self.assertEqual(
            reference.kind,
            WorkflowResourceReferenceKind.CONVENTIONAL_PACKAGE_DIRECTORY,
        )
        self.assertEqual(
            reference.conventional_directory,
            WorkflowResourceDirectory.PROMPTS,
        )

    def test_resolver_uses_only_typed_conventional_reference(self):
        reference = self.reference_factory.create("review.md")

        resolved = self.sut.resolve(self.workflow, reference)

        self.assertEqual(resolved, self.package / "prompts" / "review.md")

    def test_bare_reference_without_package_falls_back_to_declaring_directory(self):
        legacy_flow = self.root / "legacy.yaml"
        reference = self.reference_factory.create("review.md")

        resolved = self.sut.resolve(legacy_flow, reference)

        self.assertEqual(resolved, self.root / "review.md")

    def test_rejects_declaring_relative_escape_from_package(self):
        reference = self.reference_factory.create("../outside.md")

        with self.assertRaises(FlowValidationError):
            self.sut.resolve(self.workflow, reference)

    def test_rejects_package_reference_without_owning_package(self):
        legacy_flow = self.root / "legacy.yaml"
        reference = self.reference_factory.create("$package/review.md")

        with self.assertRaises(FlowValidationError):
            self.sut.resolve(legacy_flow, reference)


if __name__ == "__main__":
    unittest.main()
