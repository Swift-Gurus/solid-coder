"""Locks the precedence of overlapping prepared search evidence."""

import unittest

from source.exact_source_search_match_kind_resolver import ExactSourceSearchMatchKindResolver
from source.source_search_evidence import SourceSearchEvidence
from source.source_search_match import SourceSearchMatch
from source.source_search_match_kind import SourceSearchMatchKind


"""
solid-name: TestSourceSearchMatchPrecedence
solid-category: unit-test
solid-spec: [SPEC-060]
solid-description: Preserves classification precedence and substring fallback when search evidence overlaps.
"""
class TestSourceSearchMatchPrecedence(unittest.TestCase):
    def setUp(self) -> None:
        self.matcher = ExactSourceSearchMatchKindResolver()
        self.evidence = SourceSearchEvidence(
            filename="profile.swift",
            imports=frozenset({"profile", "foundation"}),
            frontmatter=frozenset({"profile", "foundation", "network"}),
            symbols=frozenset({"profile", "foundation", "network", "loader"}),
            content="profile foundation network loader retrieve",
        )

    def test_overlapping_evidence_preserves_existing_match_precedence(self) -> None:
        cases = [
            SourceSearchMatch(query_id="precedence", term="profile", kind=SourceSearchMatchKind.FILENAME),
            SourceSearchMatch(query_id="precedence", term="foundation", kind=SourceSearchMatchKind.IMPORT),
            SourceSearchMatch(query_id="precedence", term="network", kind=SourceSearchMatchKind.FRONTMATTER),
            SourceSearchMatch(query_id="precedence", term="loader", kind=SourceSearchMatchKind.SYMBOL),
            SourceSearchMatch(query_id="precedence", term="retr", kind=SourceSearchMatchKind.CONTENT),
        ]

        for case in cases:
            with self.subTest(term=case.term):
                self.assertEqual(self.matcher.resolve(self.evidence, case.term), case.kind)

    def test_absent_term_returns_no_match(self) -> None:
        result = self.matcher.resolve(self.evidence, "unrelated")

        self.assertIsNone(result)
