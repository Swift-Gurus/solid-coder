"""
solid-name: test_unique_string_validator
solid-category: unit-test
solid-spec: [SPEC-027, SPEC-039]
solid-description: Verifies reusable rejection of duplicate string identities with contextual errors.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.flow_validation_error import FlowValidationError
from harness.flow_validation_error_factory import FlowValidationErrorFactory
from harness.unique_string_validator import UniqueStringValidator


class TestUniqueStringValidator(unittest.TestCase):

    def setUp(self) -> None:
        self.sut = UniqueStringValidator(FlowValidationErrorFactory())

    def test_accepts_unique_values(self):
        self.sut.validate(["first", "second"], "workflow ID")

    def test_rejects_the_repeated_value_with_its_identity_name(self):
        with self.assertRaisesRegex(
            FlowValidationError,
            "Duplicate workflow ID: 'same'",
        ):
            self.sut.validate(["same", "same"], "workflow ID")


if __name__ == "__main__":
    unittest.main()
