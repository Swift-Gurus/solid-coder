"""Tests source analysis fan-out through the flow-engine operation boundary."""

from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPOSITORY_ROOT / "mcp-server"))
sys.path.insert(0, str(_REPOSITORY_ROOT / "tests" / "harness" / "flow_engine"))

from operation_workflow_integration_driver import OperationWorkflowIntegrationDriver
from harness.project_context import ProjectDirectory
from source.source_operation_registrations_factory import SourceOperationRegistrationsFactory


class TestSourceAnalysisWorkflow(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project_root = Path(temporary.name)
        self.first_path = self.project_root / "First.swift"
        self.second_path = self.project_root / "Second.swift"
        self.first_path.write_text("struct First {}\n", encoding="utf-8")
        self.second_path.write_text("actor Second {}\n", encoding="utf-8")
        self.driver = OperationWorkflowIntegrationDriver(
            project_root=self.project_root,
            registrations=SourceOperationRegistrationsFactory(
                project_directory=ProjectDirectory(path=self.project_root),
            ).make(),
        )

    def test_fans_out_analysis_and_fans_in_units_in_source_order(self) -> None:
        self.driver.write_workflow(textwrap.dedent(
            """
            name: analyze-source-files
            max_turns: 5
            steps:
              - id: select
                prompt: Select source files.
                outputs:
                  - name: sources
                    type: data
                    schema:
                      type: array
                      items:
                        type: object
              - id: analyze
                type: operation
                operation: source.analyze
                depends_on: [select]
                for_each: "{{steps.select.outputs.sources}}"
                with:
                  source: "{{item}}"
              - id: report
                depends_on: [analyze]
                prompt: "Report units: {{steps.analyze.outputs.units}}"
            """
        ))
        started = self.driver.start()

        completed = self.driver.advance({
            started.steps[0].instance_id: {
                "sources": [
                    {"kind": "file", "path": str(self.first_path)},
                    {"kind": "file", "path": str(self.second_path)},
                ]
            }
        })

        self.assertIsNone(completed.error, completed.error)
        self.assertEqual([step.step_id for step in completed.steps], ["report"])
        prompt = completed.steps[0].prompt
        self.assertLess(prompt.index("First"), prompt.index("Second"))


if __name__ == "__main__":
    unittest.main()
