"""Tests exact source-token extraction for words and compound identifiers."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from source.camel_case_identifier_segmenter import CamelCaseIdentifierSegmenter
from source.exact_source_tokens_resolver import ExactSourceTokensResolver


"""
solid-name: TestExactSourceTokensResolver
solid-category: unit-test
solid-spec: [SPEC-040]
solid-description: Verifies search tokens preserve exact identifiers while exposing deterministic CamelCase and underscore components.
"""
class TestExactSourceTokensResolver(unittest.TestCase):
    def test_preserves_exact_tokens_and_adds_identifier_components(self) -> None:
        tokens = ExactSourceTokensResolver(
            identifier_segmenter=CamelCaseIdentifierSegmenter()
        ).resolve(
            "NetworkResourceLoader remote_content"
        )

        self.assertEqual(
            tokens,
            {
                "networkresourceloader",
                "network",
                "resource",
                "loader",
                "remote_content",
                "remote",
                "content",
            },
        )

    def test_splits_acronym_boundaries_without_losing_the_identifier(self) -> None:
        tokens = ExactSourceTokensResolver(
            identifier_segmenter=CamelCaseIdentifierSegmenter()
        ).resolve("URLSessionLoader")

        self.assertEqual(
            tokens,
            {"urlsessionloader", "url", "session", "loader"},
        )


if __name__ == "__main__":
    unittest.main()
