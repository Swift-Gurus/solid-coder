"""
solid-name: test_pydantic_model_decoder
solid-category: unit-test
solid-spec: [SPEC-039]
solid-description: Verifies reusable Pydantic boundary decoding and domain validation errors.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.flow_validation_error import FlowValidationError
from harness.flow_validation_error_factory import FlowValidationErrorFactory
from harness.pydantic_model_decoder import PydanticModelDecoder
from harness.rule_declaration import RuleDeclaration


class TestPydanticModelDecoder(unittest.TestCase):

    def setUp(self) -> None:
        self.sut = PydanticModelDecoder(
            model_type=RuleDeclaration,
            error_factory=FlowValidationErrorFactory(),
        )

    def test_decodes_the_configured_model_type(self):
        rule = self.sut.decode({"tags": ["swift"]}, "workflow rule metadata")

        self.assertEqual(rule, RuleDeclaration(tags=["swift"]))

    def test_wraps_pydantic_failures_in_the_domain_error(self):
        with self.assertRaisesRegex(
            FlowValidationError,
            "Invalid workflow rule metadata",
        ):
            self.sut.decode({"unsupported": True}, "workflow rule metadata")


if __name__ == "__main__":
    unittest.main()
