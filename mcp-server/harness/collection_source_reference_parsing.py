"""Defines parsing of collection metric source references."""

from typing import Protocol

from harness.collection_source_reference import CollectionSourceReference

"""
solid-name: CollectionSourceReferenceParsing
solid-category: abstraction
solid-spec: [SPEC-053, SPEC-056]
solid-description: Parses the sealed step-output or workflow-output collection source grammar.
"""


class CollectionSourceReferenceParsing(Protocol):
    def parse(self, expression: str) -> CollectionSourceReference: ...
