"""Tests source change collection through the flow-engine operation boundary."""

from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPOSITORY_ROOT / "mcp-server"))
sys.path.insert(0, str(_REPOSITORY_ROOT / "tests" / "harness" / "flow_engine"))

from git_working_tree_fixture import GitWorkingTreeFixture
from harness.project_context import ProjectDirectory
from operation_workflow_integration_driver import OperationWorkflowIntegrationDriver
from source.source_operation_registrations_factory import SourceOperationRegistrationsFactory


class TestCollectChangesWorkflow(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project_root = Path(temporary.name)
        self.git = GitWorkingTreeFixture(self.project_root)
        self.git.initialize()
        self.git.write("Feature.swift", "struct Feature {}\n")
        self.git.run("add", ".")
        self.git.run("commit", "-m", "initial")
        self.driver = OperationWorkflowIntegrationDriver(
            project_root=self.project_root,
            registrations=SourceOperationRegistrationsFactory(
                project_directory=ProjectDirectory(path=self.project_root),
            ).make(),
        )

    def test_collects_changes_before_returning_the_dependent_agent_step(self) -> None:
        self.git.write(
            "Feature.swift",
            "struct Feature {\n    let title: String\n}\n",
        )
        self.driver.write_workflow(
            textwrap.dedent(
                """
                name: collect-source-changes
                max_turns: 5
                steps:
                  - id: collect
                    type: operation
                    operation: source.collect_changes
                    with:
                      project_root: "{{params.project_root}}"
                  - id: review
                    depends_on: [collect]
                    prompt: "Review these changes: {{steps.collect.outputs.files}}"
                """
            )
        )

        started = self.driver.start(
            params={"project_root": str(self.project_root)}
        )

        self.assertIsNone(started.error, started.error)
        self.assertEqual([step.step_id for step in started.steps], ["review"])
        self.assertIn("Feature.swift", started.steps[0].prompt)
        self.assertIn("modified", started.steps[0].prompt)


if __name__ == "__main__":
    unittest.main()
