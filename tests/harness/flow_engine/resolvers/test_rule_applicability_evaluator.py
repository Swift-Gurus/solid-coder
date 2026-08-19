"""
solid-name: test_rule_applicability_evaluator
solid-category: unit-test
solid-spec: [SPEC-039]
solid-description: Verifies rule applicability applies included/excluded extension, unit-kind, and tag selectors.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

from pydantic import TypeAdapter

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.rule_applicability_evaluator import RuleApplicabilityEvaluator
from harness.rule_applicability_context import RuleApplicabilityContext
from harness.rule_declaration import RuleDeclaration
from harness.rule_match_declaration import RuleMatchDeclaration
from harness.rule_selection import RuleSelection
from harness.rule_selection_evaluator import RuleSelectionEvaluator
from harness.rule_values_matcher import RuleValuesMatcher
from harness.rule_values_renderer import RuleValuesRenderer
from harness.strict_collection_value_matcher import StrictCollectionValueMatcher
from harness.strict_value_comparator import StrictValueComparator
from findings.review_unit_kind import ReviewUnitKind


class TestRuleApplicabilityEvaluator(unittest.TestCase):

    def setUp(self) -> None:
        comparator = StrictValueComparator()
        selection_evaluator = RuleSelectionEvaluator(
            values_matcher=RuleValuesMatcher(
                StrictCollectionValueMatcher(comparator)
            ),
            values_renderer=RuleValuesRenderer(TypeAdapter(list[str])),
        )
        self.sut = RuleApplicabilityEvaluator(selection_evaluator)

    def test_missing_included_and_excluded_values_accept_everything(self):
        decision = self.sut.evaluate(
            RuleDeclaration(),
            RuleApplicabilityContext(
                file_extension=".swift",
                unit_kind=ReviewUnitKind.STRUCT,
                tags=["ui"],
            ),
        )

        self.assertTrue(decision.applicable)

    def test_missing_file_included_means_every_extension_minus_excluded(self):
        rule = RuleDeclaration(
            match=RuleMatchDeclaration(
                file_extensions=RuleSelection(excluded=[".md"]),
            )
        )

        swift = self.sut.evaluate(rule, self._context(file_extension=".swift"))
        markdown = self.sut.evaluate(rule, self._context(file_extension=".md"))

        self.assertTrue(swift.applicable)
        self.assertFalse(markdown.applicable)

    def test_file_extension_included_values_use_any_match(self):
        rule = RuleDeclaration(
            match=RuleMatchDeclaration(
                file_extensions=RuleSelection(
                    included=[".swift", ".py"],
                ),
            )
        )

        self.assertTrue(
            self.sut.evaluate(rule, self._context(file_extension=".py")).applicable
        )
        self.assertFalse(
            self.sut.evaluate(rule, self._context(file_extension=".md")).applicable
        )

    def test_unit_kind_excluded_value_wins(self):
        rule = RuleDeclaration(
            match=RuleMatchDeclaration(
                unit_kinds=RuleSelection(
                    excluded=[ReviewUnitKind.FUNCTION],
                ),
            )
        )

        decision = self.sut.evaluate(
            rule,
            self._context(unit_kind=ReviewUnitKind.FUNCTION),
        )

        self.assertFalse(decision.applicable)

    def test_every_included_tag_must_be_detected(self):
        rule = RuleDeclaration(
            match=RuleMatchDeclaration(
                tags=RuleSelection(included=["ui", "swiftui"]),
            )
        )

        self.assertTrue(
            self.sut.evaluate(
                rule,
                self._context(tags=["view", "swiftui", "ui"]),
            ).applicable
        )

        self.assertFalse(
            self.sut.evaluate(
                rule,
                self._context(tags=["ui"]),
            ).applicable
        )

    def test_any_excluded_tag_makes_rule_inapplicable(self):
        rule = RuleDeclaration(
            match=RuleMatchDeclaration(
                tags=RuleSelection(
                    included=["ui"],
                    excluded=["test", "generated"],
                ),
            )
        )

        decision = self.sut.evaluate(
            rule,
            self._context(tags=["ui", "test"]),
        )

        self.assertFalse(decision.applicable)

    def test_tag_matching_is_exact(self):
        rule = RuleDeclaration(
            match=RuleMatchDeclaration(
                tags=RuleSelection(included=["swiftui"]),
            )
        )

        decision = self.sut.evaluate(
            rule,
            self._context(tags=["SwiftUI"]),
        )

        self.assertFalse(decision.applicable)

    def _context(
        self,
        file_extension: str = ".swift",
        unit_kind: ReviewUnitKind = ReviewUnitKind.STRUCT,
        tags: list[str] | None = None,
    ) -> RuleApplicabilityContext:
        return RuleApplicabilityContext(
            file_extension=file_extension,
            unit_kind=unit_kind,
            tags=tags or [],
        )


if __name__ == "__main__":
    unittest.main()
