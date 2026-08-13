"""
solid-name: test_script_file_resolver
solid-category: unit-test
solid-spec: [SPEC-035]
solid-description: Tests package-aware resolution of script files declared by workflow steps.
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.flow_validation_error_factory import FlowValidationErrorFactory
from harness.path_builder import PathBuilder
from harness.resolved_script_file_applier import ResolvedScriptFileApplier
from harness.resolved_step_resources_applier import ResolvedStepResourcesApplier
from harness.resolved_step_resources_factory import ResolvedStepResourcesFactory
from harness.script_file_resolver import ScriptFileResolver
from harness.step_declaring_file_resolver import StepDeclaringFileResolver
from harness.step_declaration import StepDeclaration
from harness.workflow_package_root_locator import WorkflowPackageRootLocator
from harness.workflow_resource_directory import WorkflowResourceDirectory
from harness.workflow_resource_path_classifier import WorkflowResourcePathClassifier
from harness.workflow_resource_path_resolver import WorkflowResourcePathResolver
from harness.workflow_resource_reference_factory import WorkflowResourceReferenceFactory


class TestScriptFileResolver(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.package = Path(self.temporary_directory.name) / "review"
        self.package.mkdir()
        self.workflow = self.package / "workflow.yaml"
        self.workflow.write_text("id: review\n")
        error_factory = FlowValidationErrorFactory()
        path_resolver = WorkflowResourcePathResolver(
            WorkflowPackageRootLocator(),
            error_factory,
        )
        reference_factory = WorkflowResourceReferenceFactory(
            WorkflowResourcePathClassifier(),
            WorkflowResourceDirectory.SCRIPTS,
        )
        self.sut = ScriptFileResolver(
            StepDeclaringFileResolver(PathBuilder()),
            path_resolver,
            reference_factory,
            ResolvedScriptFileApplier(
                ResolvedStepResourcesFactory(),
                ResolvedStepResourcesApplier(),
            ),
        )

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_resolves_bare_file_from_package_scripts_directory(self):
        resolved = self.sut.resolve(
            StepDeclaration(
                id="validate",
                type="script",
                script_file_reference="validate.py",
            ),
            str(self.workflow),
        )

        self.assertEqual(
            resolved.script_file,
            str((self.package / "scripts" / "validate.py").resolve()),
        )
        self.assertIsNone(resolved.script_file_reference)

    def test_resolves_package_root_reference(self):
        resolved = self.sut.resolve(
            StepDeclaration(
                id="validate",
                type="script",
                script_file_reference="$package/custom/validate.py",
            ),
            str(self.workflow),
        )

        self.assertEqual(
            resolved.script_file,
            str((self.package / "custom" / "validate.py").resolve()),
        )

    def test_resolves_explicit_relative_file_from_declaring_yaml(self):
        nested = self.package / "steps" / "fragment.yaml"
        nested.parent.mkdir()
        nested.write_text("id: fragment\n")
        resolved = self.sut.resolve(
            StepDeclaration(
                id="validate",
                type="script",
                script_file_reference="../scripts/validate.py",
                source_file=str(nested),
            ),
            str(self.workflow),
        )

        self.assertEqual(
            resolved.script_file,
            str((self.package / "scripts" / "validate.py").resolve()),
        )

    def test_leaves_steps_without_file_unchanged(self):
        step = StepDeclaration(
            id="legacy",
            type="script",
            command=["bash", "check.sh"],
        )

        self.assertIs(self.sut.resolve(step, str(self.workflow)), step)


if __name__ == "__main__":
    unittest.main()
