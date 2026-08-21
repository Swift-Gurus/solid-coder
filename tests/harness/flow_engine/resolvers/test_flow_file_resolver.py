"""
solid-name: test_flow_file_resolver
solid-category: unit-test
solid-spec: [SPEC-031]
solid-description: Tests resolving a flow name to a concrete YAML path across search directories, with literal-path fallback.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.existing_path_filter import ExistingPathFilter
from harness.flow_file_resolver import FlowFileResolver
from harness.flow_search_path_resolver import FlowSearchPathResolver
from harness.models import FlowValidationError
from harness.path_checking import PathChecker
from harness.plugin_workflow_search_path_resolver import PluginWorkflowSearchPathResolver
from harness.workflow_catalog_factory import WorkflowCatalogFactory


class TestFlowFileResolver(unittest.TestCase):

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self.project_dir = Path(self._tmpdir) / "project"
        self.plugin_dir = Path(self._tmpdir) / "plugin"
        self.project_dir.mkdir(parents=True)
        self.plugin_dir.mkdir(parents=True)
        self.sut = FlowFileResolver(
            path_checker=_RealPathChecker(),
            catalog_resolver=WorkflowCatalogFactory().make(),
        )

    def test_resolves_package_id_in_first_search_dir(self):
        flow_file = self._package(self.project_dir, "code-review")

        result = self.sut.resolve("code-review", [str(self.project_dir), str(self.plugin_dir)])

        self.assertEqual(result, str(flow_file.resolve()))

    def test_flat_yaml_is_not_catalog_discoverable(self):
        flow_file = self.project_dir / "code_review.yml"
        flow_file.write_text("name: code_review\nsteps: []\n")

        result = self.sut.resolve("code_review", [str(self.project_dir), str(self.plugin_dir)])

        self.assertEqual(result, "code_review")

    def test_duplicate_ids_across_search_dirs_are_rejected(self):
        project_file = self._package(self.project_dir, "code-review")
        plugin_file = self._package(self.plugin_dir, "code-review")

        with self.assertRaises(FlowValidationError) as ctx:
            self.sut.resolve("code-review", [str(self.project_dir), str(self.plugin_dir)])

        self.assertIn(str(project_file.resolve()), str(ctx.exception))
        self.assertIn(str(plugin_file.resolve()), str(ctx.exception))

    def test_falls_back_to_second_search_dir_when_first_has_no_match(self):
        plugin_file = self._package(self.plugin_dir, "code-review")

        result = self.sut.resolve("code-review", [str(self.project_dir), str(self.plugin_dir)])

        self.assertEqual(result, str(plugin_file.resolve()))

    def test_returns_literal_flow_unchanged_when_no_search_dir_matches(self):
        literal_path = str(Path(self._tmpdir) / "somewhere" / "custom.yaml")

        result = self.sut.resolve(literal_path, [str(self.project_dir), str(self.plugin_dir)])

        self.assertEqual(result, literal_path)

    def test_returns_literal_flow_unchanged_when_no_search_paths_given(self):
        result = self.sut.resolve("code_review", [])

        self.assertEqual(result, "code_review")

    def test_resolves_nested_package_by_declared_id(self):
        package = self.project_dir / "review" / "api"
        package.mkdir(parents=True)
        entrypoint = package / "workflow.yaml"
        entrypoint.write_text(
            "id: acme-api-review\n"
            "name: API Review\n"
            "max_turns: 10\n"
            "steps:\n"
            "  - id: review\n"
            "    prompt: Review the API\n"
        )

        result = self.sut.resolve("acme-api-review", [str(self.project_dir), str(self.plugin_dir)])

        self.assertEqual(result, str(entrypoint.resolve()))

    def test_multiple_packages_in_one_category_resolve_independently(self):
        review = self.project_dir / "review"
        first = review / "api" / "workflow.yaml"
        second = review / "security" / "workflow.yaml"
        first.parent.mkdir(parents=True)
        second.parent.mkdir(parents=True)
        first.write_text("id: api-review\nname: API Review\nmax_turns: 5\nsteps: [{id: run, prompt: Run}]\n")
        second.write_text("id: security-review\nname: Security Review\nmax_turns: 5\nsteps: [{id: run, prompt: Run}]\n")

        first_result = self.sut.resolve("api-review", [str(self.project_dir)])
        second_result = self.sut.resolve("security-review", [str(self.project_dir)])

        self.assertEqual(first_result, str(first.resolve()))
        self.assertEqual(second_result, str(second.resolve()))

    def test_discovers_a_workflow_added_after_an_earlier_lookup(self):
        first = self._package(self.project_dir, "first")

        first_result = self.sut.resolve("first", [str(self.project_dir)])

        second = self._package(self.project_dir, "second")
        second_result = self.sut.resolve("second", [str(self.project_dir)])

        self.assertEqual(first_result, str(first.resolve()))
        self.assertEqual(second_result, str(second.resolve()))

    def test_discovers_plugin_package_but_not_flat_legacy_workflow(self):
        package = self.plugin_dir / "workflows" / "review" / "plugin-package" / "workflow.yaml"
        package.parent.mkdir(parents=True)
        package.write_text(
            "id: plugin-package\n"
            "name: Plugin Package\n"
            "max_turns: 2\n"
            "steps: [{id: run, prompt: Run}]\n"
        )
        legacy = self.plugin_dir / ".solid-coder" / "harness" / "flows" / "plugin-legacy.yaml"
        legacy.parent.mkdir(parents=True)
        legacy.write_text("name: plugin_legacy\nsteps: [{id: run, prompt: Run}]\n")

        search_paths = self._plugin_search_paths()

        self.assertEqual(self.sut.resolve("plugin-package", search_paths), str(package.resolve()))
        self.assertEqual(self.sut.resolve("plugin-legacy", search_paths), "plugin-legacy")

    def test_flat_legacy_workflow_does_not_collide_with_a_package_id(self):
        package = self.plugin_dir / "workflows" / "review" / "duplicate" / "workflow.yaml"
        package.parent.mkdir(parents=True)
        package.write_text(
            "id: duplicate\n"
            "name: Package Duplicate\n"
            "max_turns: 2\n"
            "steps: [{id: run, prompt: Run}]\n"
        )
        legacy = self.plugin_dir / ".solid-coder" / "harness" / "flows" / "duplicate.yaml"
        legacy.parent.mkdir(parents=True)
        legacy.write_text("name: legacy_duplicate\nsteps: [{id: run, prompt: Run}]\n")

        result = self.sut.resolve("duplicate", self._plugin_search_paths())

        self.assertEqual(result, str(package.resolve()))

    def _plugin_search_paths(self) -> list[str]:
        resolver = FlowSearchPathResolver(
            sources=[PluginWorkflowSearchPathResolver(self.plugin_dir)],
            path_filter=ExistingPathFilter(PathChecker()),
        )
        return [str(path) for path in resolver.resolve()]

    @staticmethod
    def _package(root: Path, workflow_id: str) -> Path:
        entrypoint = root / workflow_id / "workflow.yaml"
        entrypoint.parent.mkdir(parents=True)
        entrypoint.write_text(
            f"id: {workflow_id}\n"
            f"name: {workflow_id}\n"
            "max_turns: 2\n"
            "steps: [{id: run, prompt: Run}]\n"
        )
        return entrypoint


class _RealPathChecker:
    def exists(self, path: str) -> bool:
        return Path(path).exists()


if __name__ == "__main__":
    unittest.main()
