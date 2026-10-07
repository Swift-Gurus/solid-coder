"""Adapts source text to an injected syntax parser."""

from typing import Protocol, TypeVar

from tree_sitter import Tree


SourceInput = TypeVar("SourceInput", contravariant=True)
SyntaxOutput = TypeVar("SyntaxOutput", covariant=True)


"""
solid-name: SourceSyntaxParsing
solid-category: abstraction
solid-spec: [SPEC-057]
solid-description: Contract for parsing source into a syntax tree.
"""
class SourceSyntaxParsing(Protocol[SourceInput, SyntaxOutput]):
    def parse(self, source: SourceInput) -> SyntaxOutput: ...


"""
solid-name: TreeSitterSyntaxParser
solid-category: adapter
solid-spec: [SPEC-057]
solid-description: Parses source text into a syntax tree.
"""
class TreeSitterSyntaxParser(SourceSyntaxParsing[str, Tree]):
    def __init__(self, parser: SourceSyntaxParsing[bytes, Tree]) -> None:
        self._parser = parser

    def parse(self, source: str) -> Tree:
        return self._parser.parse(source.encode("utf-8"))
