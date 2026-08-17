"""
solid-name: test_workflow_package_catalog_document
solid-category: unit-test
solid-spec: [SPEC-035, SPEC-039]
solid-description: Verifies package catalog fields and rule enrollment decode through the shared model boundary.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.flow_validation_error import FlowValidationError
from harness.flow_validation_error_factory import FlowValidationErrorFactory
from harness.pydantic_model_decoder import PydanticModelDecoder
from harness.workflow_package_catalog_document import WorkflowPackageCatalogDocument


class TestWorkflowPackageCatalogDocument(unittest.TestCase):

    def setUp(self) -> None:
        self.sut = PydanticModelDecoder(
            model_type=WorkflowPackageCatalogDocument,
            error_factory=FlowValidationErrorFactory(),
        )

    def test_decodes_empty_rule_marker_and_optional_metadata(self):
        document = self.sut.decode(
            self._workflow(rule={"category": "quality", "tags": ["swift"]}),
            "workflow package",
        )

        self.assertEqual(document.id, "acme-review")
        self.assertEqual(document.rule.category, "quality")
        self.assertEqual(document.rule.tags, ["swift"])

    def test_omitted_rule_marker_remains_an_ordinary_workflow(self):
        document = self.sut.decode(self._workflow(), "workflow package")

        self.assertIsNone(document.rule)

    def test_unknown_rule_fields_are_rejected(self):
        with self.assertRaisesRegex(FlowValidationError, "Invalid workflow package"):
            self.sut.decode(
                self._workflow(rule={"unsupported": True}),
                "workflow package",
            )

    def test_invalid_package_catalog_fields_are_rejected(self):
        with self.assertRaisesRegex(FlowValidationError, "Invalid workflow package"):
            self.sut.decode(
                {"id": "Invalid ID", "name": "", "max_turns": 0, "steps": []},
                "workflow package",
            )

    @staticmethod
    def _workflow(rule: object | None = None) -> dict:
        workflow = {
            "id": "acme-review",
            "name": "ACME Review",
            "description": "Additional workflow root fields remain available.",
            "max_turns": 3,
            "steps": [{"id": "review", "prompt": "Review the unit."}],
        }
        if rule is not None:
            workflow["rule"] = rule
        return workflow


if __name__ == "__main__":
    unittest.main()
