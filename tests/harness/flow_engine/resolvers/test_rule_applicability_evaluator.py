"""
solid-name: test_rule_applicability_evaluator
solid-category: unit-test
solid-spec: [SPEC-039]
solid-description: Verifies rule applicability uses exact all-required matching against MCP-detected unit tags.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.rule_applicability_evaluator import RuleApplicabilityEvaluator
from harness.rule_declaration import RuleDeclaration


class TestRuleApplicabilityEvaluator(unittest.TestCase):

    def setUp(self) -> None:
        self.sut = RuleApplicabilityEvaluator()

    def test_empty_required_tags_are_always_applicable(self):
        self.assertTrue(self.sut.is_applicable(RuleDeclaration(), []))

    def test_every_required_tag_must_be_detected(self):
        rule = RuleDeclaration(tags=["swift", "swiftui"])

        self.assertTrue(
            self.sut.is_applicable(rule, ["view", "swiftui", "swift"])
        )

    def test_one_missing_required_tag_makes_the_rule_inapplicable(self):
        rule = RuleDeclaration(tags=["swift", "swiftui"])

        self.assertFalse(self.sut.is_applicable(rule, ["swift"]))

    def test_tag_matching_is_exact(self):
        rule = RuleDeclaration(tags=["swiftui"])

        self.assertFalse(self.sut.is_applicable(rule, ["SwiftUI"]))


if __name__ == "__main__":
    unittest.main()
