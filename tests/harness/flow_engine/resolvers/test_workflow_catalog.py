"""
solid-name: test_workflow_catalog
solid-category: unit-test
solid-spec: [SPEC-035, SPEC-039]
solid-description: Verifies deterministic enrollment of typed rule workflow sources.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.rule_declaration import RuleDeclaration
from harness.rule_match_declaration import RuleMatchDeclaration
from harness.rule_selection import RuleSelection
from harness.workflow_catalog import WorkflowCatalog
from harness.workflow_source import WorkflowSource


class TestWorkflowCatalog(unittest.TestCase):

    def test_rule_sources_excludes_ordinary_workflows_and_orders_by_workflow_id(self):
        ordinary = self._source("ordinary")
        later = self._source("z-rule", RuleDeclaration())
        earlier = self._source(
            "a-rule",
            RuleDeclaration(
                match=RuleMatchDeclaration(
                    tags=RuleSelection(included=["swift"])
                )
            ),
        )
        sut = WorkflowCatalog(
            sources=[ordinary, later, earlier]
        )

        rules = sut.rule_sources()

        self.assertEqual(rules, [earlier, later])

    @staticmethod
    def _source(
        workflow_id: str,
        rule: RuleDeclaration | None = None,
    ) -> WorkflowSource:
        return WorkflowSource(
            id=workflow_id,
            entry_path=Path(f"/{workflow_id}/workflow.yaml"),
            package_root=Path(f"/{workflow_id}"),
            rule=rule,
        )


if __name__ == "__main__":
    unittest.main()
