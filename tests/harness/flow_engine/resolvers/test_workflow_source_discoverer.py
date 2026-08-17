"""
solid-name: test_workflow_source_discoverer
solid-category: unit-test
solid-spec: [SPEC-035, SPEC-039]
solid-description: Verifies package discovery consumes the validator's typed workflow source.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.rule_declaration import RuleDeclaration
from harness.package_workflow_source_discoverer import PackageWorkflowSourceDiscoverer
from harness.workflow_source import WorkflowSource
from harness.workflow_package_catalog_document import WorkflowPackageCatalogDocument


class StubConfigFileLoader:
    def __init__(self, document: dict) -> None:
        self._document = document

    def load(self, path: Path) -> dict:
        return self._document


class StubWorkflowPackageDecoder:
    def __init__(self, document: WorkflowPackageCatalogDocument) -> None:
        self._document = document

    def decode(self, value: object, description: str) -> WorkflowPackageCatalogDocument:
        return self._document


class TestWorkflowSourceDiscoverer(unittest.TestCase):

    def test_uses_the_typed_source_returned_by_package_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / "quality"
            package.mkdir()
            entry_path = package / "workflow.yaml"
            entry_path.touch()
            document = WorkflowPackageCatalogDocument(
                id="acme-quality",
                name="ACME Quality",
                max_turns=2,
                steps=[object()],
                rule=RuleDeclaration(tags=["swift"]),
            )
            sut = PackageWorkflowSourceDiscoverer(
                file_loader=StubConfigFileLoader({"id": "unvalidated-id"}),
                document_decoder=StubWorkflowPackageDecoder(document),
            )

            sources = sut.discover(root)

        self.assertEqual(
            sources,
            [
                WorkflowSource(
                    id="acme-quality",
                    entry_path=entry_path.resolve(),
                    package_root=package.resolve(),
                    rule=document.rule,
                )
            ],
        )
        self.assertEqual(sources[0].rule.tags, ["swift"])


if __name__ == "__main__":
    unittest.main()
