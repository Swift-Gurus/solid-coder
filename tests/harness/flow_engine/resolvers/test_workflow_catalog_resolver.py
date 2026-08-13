"""
solid-name: test_workflow_catalog_resolver
solid-category: unit-test
solid-spec: [SPEC-035]
solid-description: Verifies catalog reuse within one flow-definition load and refresh across separate loads.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.workflow_catalog import WorkflowCatalog
from harness.workflow_catalog_resolver import WorkflowCatalogResolver
from harness.workflow_source import WorkflowSource


class RecordingCatalogBuilder:
    def __init__(self, catalogs: list[WorkflowCatalog]) -> None:
        self._catalogs = catalogs
        self.calls: list[list[Path]] = []

    def build(self, roots: list[Path]) -> WorkflowCatalog:
        self.calls.append(roots)
        return self._catalogs[len(self.calls) - 1]


class TestWorkflowCatalogResolver(unittest.TestCase):

    def test_reuses_one_catalog_for_all_lookups_within_a_load(self):
        source = self._source("/first/workflow.yaml")
        builder = RecordingCatalogBuilder([WorkflowCatalog(sources={"review": source})])
        sut = WorkflowCatalogResolver(builder)

        with sut.scope(["/workflows"]):
            first = sut.resolve("review", ["/workflows"])
            second = sut.resolve("review", ["/workflows"])

        self.assertIs(first, source)
        self.assertIs(second, source)
        self.assertEqual(builder.calls, [[Path("/workflows")]])

    def test_rebuilds_the_catalog_for_each_separate_load(self):
        first_source = self._source("/first/workflow.yaml")
        second_source = self._source("/second/workflow.yaml")
        builder = RecordingCatalogBuilder([
            WorkflowCatalog(sources={"review": first_source}),
            WorkflowCatalog(sources={"review": second_source}),
        ])
        sut = WorkflowCatalogResolver(builder)

        with sut.scope(["/workflows"]):
            first = sut.resolve("review", ["/workflows"])
        with sut.scope(["/workflows"]):
            second = sut.resolve("review", ["/workflows"])

        self.assertIs(first, first_source)
        self.assertIs(second, second_source)
        self.assertEqual(builder.calls, [[Path("/workflows")], [Path("/workflows")]])

    def test_unscoped_lookups_never_reuse_a_catalog(self):
        first_source = self._source("/first/workflow.yaml")
        second_source = self._source("/second/workflow.yaml")
        builder = RecordingCatalogBuilder([
            WorkflowCatalog(sources={"review": first_source}),
            WorkflowCatalog(sources={"review": second_source}),
        ])
        sut = WorkflowCatalogResolver(builder)

        first = sut.resolve("review", ["/workflows"])
        second = sut.resolve("review", ["/workflows"])

        self.assertIs(first, first_source)
        self.assertIs(second, second_source)
        self.assertEqual(builder.calls, [[Path("/workflows")], [Path("/workflows")]])

    def test_does_not_build_a_catalog_when_a_load_performs_no_id_lookup(self):
        builder = RecordingCatalogBuilder([])
        sut = WorkflowCatalogResolver(builder)

        with sut.scope([]):
            pass

        self.assertEqual(builder.calls, [])

    @staticmethod
    def _source(entry_path: str) -> WorkflowSource:
        return WorkflowSource(
            id="review",
            entry_path=Path(entry_path),
            package_root=None,
        )


if __name__ == "__main__":
    unittest.main()
