"""Loads top-level items from Swift parser documents."""

from harness.json_loading import JsonLoading
from source.source_operation_error import SourceOperationError
from source.swift_ast_items_loading import SwiftASTItemsLoading


"""
solid-name: SwiftASTItemsLoader
solid-category: boundary-adapter
solid-spec: [SPEC-040]
solid-description: Loads and validates the ordered top-level item collection from a Swift parser document.
"""
class SwiftASTItemsLoader(SwiftASTItemsLoading):
    def __init__(self, json_loader: JsonLoading) -> None:
        self._json_loader = json_loader

    def load(self, parser_document: str) -> list[object]:
        try:
            document = self._json_loader.safe_load(parser_document)
            items = document["items"]
        except (ValueError, KeyError, TypeError) as error:
            raise SourceOperationError(
                f"Swift parser returned invalid output: {error}"
            ) from error
        if not isinstance(items, list):
            raise SourceOperationError(
                "Swift parser returned an invalid top-level item collection"
            )
        return items
