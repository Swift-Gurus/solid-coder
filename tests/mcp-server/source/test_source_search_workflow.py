"""Tests source search and candidate loading through flow-engine replay."""

from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import Mock

_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPOSITORY_ROOT / "mcp-server"))
sys.path.insert(0, str(_REPOSITORY_ROOT / "tests" / "harness" / "flow_engine"))

from harness.operation_registration import OperationRegistration
from harness.project_context import ProjectDirectory
from operation_workflow_integration_driver import OperationWorkflowIntegrationDriver
from source.read_source_candidates_input import ReadSourceCandidatesInput
from source.read_source_candidates_operation_factory import (
    ReadSourceCandidatesOperationFactory,
)
from source.read_source_candidates_output import ReadSourceCandidatesOutput
from source.source_search_input import SourceSearchInput
from source.source_search_operation_factory import SourceSearchOperationFactory
from source.source_search_output import SourceSearchOutput
from source.search_target_granularity import SearchTargetGranularity


"""
solid-name: TestSourceSearchWorkflow
solid-category: integration-test
solid-spec: [SPEC-010, SPEC-040]
solid-description: Proves source search and candidate reads drain internally and replay persisted outputs without filesystem access.
"""
class TestSourceSearchWorkflow(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project_root = Path(temporary.name)
        self.candidate_path = self.project_root / "Sources" / "TaxRule.swift"
        self.candidate_path.parent.mkdir(parents=True)
        self.candidate_path.write_text(
            "struct TaxRule { let invoice: String }\n",
            encoding="utf-8",
        )
        project_directory = ProjectDirectory(path=self.project_root)
        self.search = Mock(wraps=SourceSearchOperationFactory().make(
            project_directory,
            SearchTargetGranularity.UNIT,
        ))
        self.reader = Mock(wraps=ReadSourceCandidatesOperationFactory(
            project_directory
        ).make())
        self.driver = OperationWorkflowIntegrationDriver(
            project_root=self.project_root,
            registrations=[
                OperationRegistration(
                    name="source.search",
                    input_model=SourceSearchInput,
                    output_model=SourceSearchOutput,
                    handler=self.search,
                ),
                OperationRegistration(
                    name="source.read_candidates",
                    input_model=ReadSourceCandidatesInput,
                    output_model=ReadSourceCandidatesOutput,
                    handler=self.reader,
                ),
            ],
        )
        self.driver.write_workflow(textwrap.dedent(
            """
            name: source-search-replay
            max_turns: 5
            steps:
              - id: search
                type: operation
                operation: source.search
                with:
                  queries: "{{params.queries}}"
              - id: read
                type: operation
                operation: source.read_candidates
                depends_on: [search]
                with:
                  candidates: "{{steps.search.outputs.candidates}}"
              - id: report
                depends_on: [read]
                prompt: "Compare {{steps.read.outputs.results}}"
            """
        ))

    def test_replays_exact_candidate_content_without_searching_or_reading_again(self) -> None:
        started = self.driver.start(params={
            "queries": [{"id": "tax", "terms": ["TaxRule"]}],
        })

        self.assertIsNone(started.error, started.error)
        self.assertIn("struct TaxRule", started.steps[0].prompt)
        self.assertEqual(self.search.execute.call_count, 1)
        self.assertEqual(self.reader.execute.call_count, 1)
        self.candidate_path.write_text("struct Changed {}\n", encoding="utf-8")

        completed = self.driver.advance({started.steps[0].instance_id: {}})

        self.assertEqual(completed.status, "done")
        self.assertEqual(self.search.execute.call_count, 1)
        self.assertEqual(self.reader.execute.call_count, 1)


if __name__ == "__main__":
    unittest.main()
