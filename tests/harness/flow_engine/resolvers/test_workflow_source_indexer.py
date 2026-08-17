"""
solid-name: test_workflow_source_indexer
solid-category: unit-test
solid-spec: [SPEC-035, SPEC-039]
solid-description: Verifies deterministic collision-checked workflow source ordering without map-based output.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.flow_validation_error import FlowValidationError
from harness.workflow_source import WorkflowSource
from harness.workflow_source_indexer import WorkflowSourceIndexer


class TestWorkflowSourceIndexer(unittest.TestCase):

    def test_returns_sources_in_stable_workflow_id_order(self):
        later = self._source("z-rule", "/z/workflow.yaml")
        earlier = self._source("a-rule", "/a/workflow.yaml")

        sources = WorkflowSourceIndexer().index([later, earlier])

        self.assertEqual(sources, [earlier, later])

    def test_reports_every_path_for_a_duplicate_workflow_id(self):
        first = self._source("same-rule", "/first/workflow.yaml")
        second = self._source("same-rule", "/second/workflow.yaml")

        with self.assertRaisesRegex(
            FlowValidationError,
            "/first/workflow.yaml, /second/workflow.yaml",
        ):
            WorkflowSourceIndexer().index([second, first])

    @staticmethod
    def _source(workflow_id: str, path: str) -> WorkflowSource:
        return WorkflowSource(
            id=workflow_id,
            entry_path=Path(path),
            package_root=None,
        )


if __name__ == "__main__":
    unittest.main()
