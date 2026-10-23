"""
solid-name: TestTreeSitterLeadingCommentsParser
solid-category: unit-test
solid-spec: [SPEC-069]
solid-description: Verifies source comments retain declaration ownership independently of metadata names.
"""

import unittest

import tree_sitter_swift
from source.analysis.declarations.tree_sitter_leading_comments_parser import (
    TreeSitterLeadingCommentsParser,
)
from source.analysis.tree_sitter_node_span_parser import TreeSitterNodeSpanParser
from source.analysis.tree_sitter_nodes_parser import TreeSitterNodesParser
from source.source_evidence import SourceEvidence
from source.source_line_range import SourceLineRange
from tree_sitter import Language, Parser


class TestTreeSitterLeadingCommentsParser(unittest.TestCase):
    def setUp(self) -> None:
        self.syntax = Parser(Language(tree_sitter_swift.language()))
        self.nodes = TreeSitterNodesParser(
            excluded_node_types=frozenset(),
            excluded_fields=frozenset(),
        )
        self.sut = TreeSitterLeadingCommentsParser(
            spans=TreeSitterNodeSpanParser(),
            comment_node_types=frozenset({"comment", "multiline_comment"}),
        )

    def test_preserves_comment_ownership_when_metadata_name_is_wrong(self) -> None:
        comments = self._comments("/** solid-name: Wrong */\nstruct Target {}")

        self.assertEqual(
            comments,
            [
                SourceEvidence(
                    fact="/** solid-name: Wrong */",
                    span=SourceLineRange(start=1, end=1),
                )
            ],
        )

    def test_retains_contiguous_comment_blocks_in_source_order(self) -> None:
        comments = self._comments(
            "/// First\n/** Second */\n// Third\nstruct Target {}",
        )

        self.assertEqual(
            [entry.fact for entry in comments],
            [
                "/// First",
                "/** Second */",
                "// Third",
            ],
        )

    def test_does_not_borrow_another_declarations_comments(self) -> None:
        comments = self._comments(
            "// solid-name: Earlier\nstruct Earlier {}\nstruct Target {}",
        )

        self.assertEqual(comments, [])

    def test_does_not_treat_a_string_as_an_attached_comment(self) -> None:
        comments = self._comments(
            'let text = "solid-name: Target"\nstruct Target {}',
        )

        self.assertEqual(comments, [])

    def test_stops_at_intervening_source_tokens(self) -> None:
        comments = self._comments(
            "/** solid-name: Target */; struct Target {}",
        )

        self.assertEqual(comments, [])

    def test_attaches_comments_before_declaration_attributes(self) -> None:
        comments = self._comments(
            "// solid-name: Target\n@MainActor final class Target {}",
        )

        self.assertEqual([entry.fact for entry in comments], ["// solid-name: Target"])

    def test_retains_nested_declaration_comment_spans(self) -> None:
        comments = self._comments(
            "struct Outer {\n/**\n solid-name: Target\n */\n struct Target {}\n}",
        )

        self.assertEqual(
            comments,
            [
                SourceEvidence(
                    fact="/**\n solid-name: Target\n */",
                    span=SourceLineRange(start=2, end=4),
                )
            ],
        )

    def test_unicode_does_not_shift_comment_association(self) -> None:
        comments = self._comments(
            'let label = "é 🐈"\n// solid-description: Décrit une capacité.\nstruct Target {}',
        )

        self.assertEqual(
            comments,
            [
                SourceEvidence(
                    fact="// solid-description: Décrit une capacité.",
                    span=SourceLineRange(start=2, end=2),
                )
            ],
        )

    def _comments(self, text: str) -> list[SourceEvidence]:
        tree = self.syntax.parse(text.encode("utf-8"))
        declaration = next(
            node
            for node in self.nodes.parse(tree.root_node)
            if node.type == "class_declaration"
            and node.child_by_field_name("name").text == b"Target"
        )
        return self.sut.parse(declaration)
