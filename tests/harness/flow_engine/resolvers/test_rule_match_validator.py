"""
solid-name: test_rule_match_validator
solid-category: unit-test
solid-spec: [SPEC-039]
solid-description: Verifies review-rule matcher declarations reject ambiguous or non-normalized selectors.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.flow_validation_error import FlowValidationError
from harness.flow_validation_error_factory import FlowValidationErrorFactory
from harness.rule_match_declaration import RuleMatchDeclaration
from harness.rule_match_validator import RuleMatchValidator
from harness.rule_selection import RuleSelection


class TestRuleMatchValidator(unittest.TestCase):

    def setUp(self) -> None:
        self.sut = RuleMatchValidator(FlowValidationErrorFactory())

    def test_accepts_empty_and_normalized_matchers(self):
        self.sut.validate(
            RuleMatchDeclaration(
                file_extensions=RuleSelection(included=[".swift", ".py"]),
                tags=RuleSelection(
                    included=["ui"],
                    excluded=["test"],
                ),
            )
        )

    def test_rejects_duplicate_values(self):
        with self.assertRaisesRegex(FlowValidationError, "duplicate"):
            self.sut.validate(
                RuleMatchDeclaration(
                    tags=RuleSelection(included=["ui", "ui"]),
                )
            )

    def test_rejects_include_exclude_intersection(self):
        with self.assertRaisesRegex(FlowValidationError, "included and excluded"):
            self.sut.validate(
                RuleMatchDeclaration(
                    tags=RuleSelection(
                        included=["test"],
                        excluded=["test"],
                    ),
                )
            )

    def test_rejects_extension_without_leading_dot(self):
        with self.assertRaisesRegex(FlowValidationError, "file extension"):
            self.sut.validate(
                RuleMatchDeclaration(
                    file_extensions=RuleSelection(included=["swift"]),
                )
            )

    def test_rejects_non_normalized_extension(self):
        with self.assertRaisesRegex(FlowValidationError, "file extension"):
            self.sut.validate(
                RuleMatchDeclaration(
                    file_extensions=RuleSelection(excluded=[".Swift"]),
                )
            )

    def test_rejects_non_normalized_tag(self):
        with self.assertRaisesRegex(FlowValidationError, "tag"):
            self.sut.validate(
                RuleMatchDeclaration(
                    tags=RuleSelection(included=["SwiftUI"]),
                )
            )


if __name__ == "__main__":
    unittest.main()
