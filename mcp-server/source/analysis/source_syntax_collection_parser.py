"""Composes syntax enumeration with typed per-entry parsing."""

from typing import Generic, TypeVar

from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing


CollectionInput = TypeVar("CollectionInput")
EntryInput = TypeVar("EntryInput")
ParsedOutput = TypeVar("ParsedOutput")


"""
solid-name: SourceSyntaxCollectionParser
solid-category: service
solid-spec: [SPEC-063]
solid-description: Recognizes typed results in ordered source-syntax collections while omitting unrecognized entries.
"""
class SourceSyntaxCollectionParser(
    SourceSyntaxParsing[CollectionInput, list[ParsedOutput]],
    Generic[CollectionInput, EntryInput, ParsedOutput],
):
    def __init__(
        self,
        entries: SourceSyntaxParsing[CollectionInput, list[EntryInput]],
        parser: SourceSyntaxParsing[EntryInput, ParsedOutput | None],
    ) -> None:
        self._entries = entries
        self._parser = parser

    def parse(self, source: CollectionInput) -> list[ParsedOutput]:
        return [
            parsed for entry in self._entries.parse(source)
            if (parsed := self._parser.parse(entry)) is not None
        ]
