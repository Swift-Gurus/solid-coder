"""Tests source analysis fan-out through the flow-engine operation boundary."""

from __future__ import annotations

import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPOSITORY_ROOT / "mcp-server"))
sys.path.insert(0, str(_REPOSITORY_ROOT / "tests" / "harness" / "flow_engine"))

from git_working_tree_fixture import GitWorkingTreeFixture
from harness.operations.operation_result import OperationResult
from harness.project_context import ProjectDirectory
from operation_workflow_integration_driver import OperationWorkflowIntegrationDriver
from source.analysis.tree_sitter_syntax_parser import TreeSitterSyntaxParser
from source.source_analysis import SourceAnalysis
from source.source_operation_registrations_factory import (
    SourceOperationRegistrationsFactory,
)

"""
solid-name: TestSourceAnalysisWorkflow
solid-category: integration-test
solid-spec: [SPEC-040, SPEC-062]
solid-description: Verifies source-analysis operation fan-out and durable member facts through workflow replay.
"""


class TestSourceAnalysisWorkflow(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project_root = Path(temporary.name).resolve()
        GitWorkingTreeFixture(self.project_root).initialize()
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

    def test_fans_out_analysis_and_fans_in_results_in_source_order(self) -> None:
        self.driver.write_workflow(
            textwrap.dedent(
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
                prompt: "Report analyses: {{steps.analyze.outputs.result}}"
            """
            )
        )
        started = self.driver.start()

        completed = self.driver.advance(
            {
                started.steps[0].instance_id: {
                    "sources": [
                        {"kind": "file", "path": str(self.first_path)},
                        {"kind": "file", "path": str(self.second_path)},
                    ]
                }
            }
        )

        self.assertIsNone(completed.error, completed.error)
        self.assertEqual([step.step_id for step in completed.steps], ["report"])
        prompt = completed.steps[0].prompt
        self.assertLess(prompt.index("First"), prompt.index("Second"))

    def test_member_facts_survive_replay_without_another_parser_execution(self) -> None:
        self.first_path.write_text(
            "protocol Contract { func read() }\n", encoding="utf-8"
        )
        self.driver.write_workflow(
            textwrap.dedent(
                """
            name: replay-source-members
            max_turns: 5
            steps:
              - id: analyze
                type: operation
                operation: source.analyze
                with:
                  source: "{{params.source}}"
              - id: report
                depends_on: [analyze]
                prompt: "Analysis: {{steps.analyze.outputs.result}}"
            """
            )
        )
        with patch.object(
            TreeSitterSyntaxParser,
            "parse",
            autospec=True,
            side_effect=TreeSitterSyntaxParser.parse,
        ) as parser:
            started = self.driver.start(
                params={
                    "source": {"kind": "file", "path": str(self.first_path)},
                }
            )
            self.assertIsNone(started.error, started.error)
            self.assertEqual(parser.call_count, 1)
            self.assertEqual([step.step_id for step in started.steps], ["report"])
            prompt = started.steps[0].prompt
            events_path = self.project_root / "runs" / started.run_id / "events.jsonl"
            events = [json.loads(line) for line in events_path.read_text().splitlines()]
            recorded = next(
                event
                for event in events
                if event.get("event") == "step_completed"
                and event.get("step_id") == "analyze"
            )
            analysis = (
                OperationResult[SourceAnalysis]
                .model_validate(recorded["outputs"])
                .result
            )
            self.assertEqual(len(analysis.units[0].members), 1)
            member = analysis.units[0].members[0]
            self.assertEqual(member.name, "read")
            self.assertEqual(member.visibility.value, "internal")
            self.assertEqual(member.kind.value, "method")
            self.assertEqual(recorded["session_id"], "engine")

            self.first_path.write_text(
                "protocol Contract { func changed() }\n", encoding="utf-8"
            )
            resumed = self.driver.advance()
            self.assertIsNone(resumed.error, resumed.error)
            self.assertEqual(resumed.steps[0].prompt, prompt)
            self.assertNotIn("changed", resumed.steps[0].prompt)
            self.assertEqual(parser.call_count, 1)

            completed = self.driver.advance({resumed.steps[0].instance_id: {}})
            self.assertIsNone(completed.error, completed.error)
            self.assertEqual(completed.status, "done")
            self.assertEqual(parser.call_count, 1)


if __name__ == "__main__":
    unittest.main()
