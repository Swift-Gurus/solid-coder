"""Measures bounded source preparation across terms and queries."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, call, patch

from harness.project_context import ProjectDirectory
from source.exact_source_tokens_resolver_factory import ExactSourceTokensResolverFactory
from source.source_search_input import SourceSearchInput
from source.source_search_operation_factory import SourceSearchOperationFactory
from source.source_search_query import SourceSearchQuery
from source.source_tokens_resolving import SourceTokensResolving


"""
solid-name: TestSourceSearchPreparation
solid-category: unit-test
solid-spec: [SPEC-060]
solid-description: Measures preparation work independently of query length while preserving query provenance and fresh source snapshots.
"""
class TestSourceSearchPreparation(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.path = self.root / "Probe.swift"
        self.content = "import Foundation\nstruct Probe { func loadProfile() {} }\n"
        self.path.write_text(self.content, encoding="utf-8")
        self.tokens = Mock(
            spec=SourceTokensResolving,
            wraps=ExactSourceTokensResolverFactory().make(),
        )
        with patch.object(ExactSourceTokensResolverFactory, "make", return_value=self.tokens):
            self.operation = SourceSearchOperationFactory().make(
                ProjectDirectory(path=self.root),
            )

    def test_38_absent_terms_tokenize_unit_content_only_once(self) -> None:
        request = SourceSearchInput(queries=[SourceSearchQuery(
            id="missing", terms=[f"absent{index}" for index in range(38)],
        )])

        result = self.operation.execute(request)

        self.assertEqual(result.candidates, [])
        self.assertEqual(self.tokens.resolve.call_args_list.count(call(self.content)), 1)
        self.assertLessEqual(self.tokens.resolve.call_count, 2)

    def test_queries_share_preparation_and_preserve_original_term_provenance(self) -> None:
        request = SourceSearchInput(queries=[
            SourceSearchQuery(id="first", terms=["profile", "PROFILE", "absent"]),
            SourceSearchQuery(id="second", terms=["Profile", "missing"]),
        ])

        result = self.operation.execute(request)

        self.assertEqual(
            [(match.query_id, match.term) for match in result.candidates[0].matches],
            [("first", "profile"), ("second", "Profile")],
        )
        self.assertEqual(self.tokens.resolve.call_args_list.count(call(self.content)), 1)

    def test_later_request_uses_changed_content_at_the_same_path(self) -> None:
        request = SourceSearchInput(queries=[SourceSearchQuery(id="profile", terms=["profile"])])

        first = self.operation.execute(request)
        self.path.write_text("struct Probe { func unrelated() {} }\n", encoding="utf-8")
        second = self.operation.execute(request)

        self.assertEqual(len(first.candidates), 1)
        self.assertEqual(second.candidates, [])

    def test_named_frontmatter_suppresses_body_only_matches_and_tokenization(self) -> None:
        documented = (
            "// solid-name: Probe\n// solid-description: Loads records.\n" + self.content
        )
        self.path.write_text(documented, encoding="utf-8")
        request = SourceSearchInput(queries=[SourceSearchQuery(id="profile", terms=["profile"])])

        result = self.operation.execute(request)

        self.assertEqual(result.candidates, [])
        self.assertNotIn(call(documented), self.tokens.resolve.call_args_list)
