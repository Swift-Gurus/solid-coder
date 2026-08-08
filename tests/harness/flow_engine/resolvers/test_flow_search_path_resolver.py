"""
solid-name: test_flow_search_path_resolver
solid-category: unit-test
solid-spec: [SPEC-031]
solid-description: Verifies project and plugin workflow search paths resolve in precedence order when project context falls back to the process working directory.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.existing_path_filter import ExistingPathFilter
from harness.flow_search_path_resolver import FlowSearchPathResolver
from harness.path_checking import PathChecker
from harness.plugin_workflow_search_path_resolver import PluginWorkflowSearchPathResolver
from harness.project_workflow_search_path_resolver import ProjectWorkflowSearchPathResolver
from hook_utils import _resolve_project_root


class TestFlowSearchPathResolver(unittest.TestCase):

    def test_uses_process_cwd_when_project_environment_is_absent(self):
        with tempfile.TemporaryDirectory() as directory:
            project_root = Path(directory)
            plugin_root = project_root / "plugin"
            project_workflows = project_root / ".solid-coder" / "harness" / "flows"
            plugin_workflows = plugin_root / "workflows"
            project_workflows.mkdir(parents=True)
            plugin_workflows.mkdir(parents=True)
            resolved_project = _resolve_project_root(
                env={},
                cwd_factory=lambda: project_root,
            )
            resolver = FlowSearchPathResolver(
                sources=[
                    ProjectWorkflowSearchPathResolver(lambda: resolved_project),
                    PluginWorkflowSearchPathResolver(plugin_root),
                ],
                path_filter=ExistingPathFilter(PathChecker()),
            )

            paths = resolver.resolve()

            self.assertEqual(paths, [project_workflows, plugin_workflows])


if __name__ == "__main__":
    unittest.main()
