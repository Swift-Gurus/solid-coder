"""Verifies codebase-search term normalization and rejection rules."""

import pytest

from search.regex_search_term_extractor import RegexSearchTermExtractor
from search.search_terms_resolver import SearchTermsResolver


"""
solid-name: TestSearchTermsResolver
solid-category: unit-test
solid-description: Verifies codebase-search inputs resolve to individual terms or fail with actionable errors.
"""
class TestSearchTermsResolver:
    def setup_method(self) -> None:
        self.resolver = SearchTermsResolver(RegexSearchTermExtractor())

    def test_query_resolves_to_individual_terms(self) -> None:
        assert self.resolver.resolve("Batch handler, routing", None) == [
            "Batch",
            "handler",
            "routing",
        ]

    def test_individual_tags_remain_supported(self) -> None:
        assert self.resolver.resolve(None, ["Batch", "handler", "routing"]) == [
            "Batch",
            "handler",
            "routing",
        ]

    def test_query_and_tags_are_mutually_exclusive(self) -> None:
        with pytest.raises(ValueError, match="query or tags"):
            self.resolver.resolve("Batch handler", ["routing"])

    def test_aggregated_query_inside_tags_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="each tags entry must be one term"):
            self.resolver.resolve(None, ["Batch handler routing"])

    def test_blank_query_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="at least one searchable term"):
            self.resolver.resolve(" -- ", None)
