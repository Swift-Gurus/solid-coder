"""
solid-name: test_workflow_catalog_factory
solid-category: unit-test
solid-spec: [SPEC-035]
solid-description: Verifies concrete workflow catalog factories compose the production builder and resolver.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.workflow_catalog_factory import WorkflowCatalogFactory
from harness.workflow_catalog_resolver import WorkflowCatalogResolver


class TestWorkflowCatalogFactory(unittest.TestCase):

    def test_factory_makes_workflow_catalog_resolver(self) -> None:
        self.assertIsInstance(
            WorkflowCatalogFactory().make(),
            WorkflowCatalogResolver,
        )


if __name__ == "__main__":
    unittest.main()
