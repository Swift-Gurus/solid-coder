"""Reads discovered source metadata through injected document and decoding boundaries."""

from harness.flow_validation_error import FlowValidationError
from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing
from source.source_frontmatter import SourceFrontmatter
from source.source_frontmatter_reading import SourceFrontmatterReading


"""
solid-name: SourceFrontmatterReader
solid-category: service
solid-spec: [SPEC-040, SPEC-069]
solid-description: Provides ordered source metadata with strict declaration validation and tolerant repository discovery.
"""
class SourceFrontmatterReader(SourceFrontmatterReading, SourceSyntaxParsing[str, SourceFrontmatter | None]):
    def __init__(
        self,
        documents: SourceSyntaxParsing[str, list[str]],
        decoder: SourceSyntaxParsing[str, SourceFrontmatter],
    ) -> None:
        self._documents = documents
        self._decoder = decoder

    def read(self, content: str) -> list[SourceFrontmatter]:
        frontmatters: list[SourceFrontmatter] = []
        for document in self._documents.parse(content):
            try:
                frontmatters.append(self._decoder.parse(document))
            except FlowValidationError:
                continue
        return frontmatters

    def parse(self, source: str) -> SourceFrontmatter | None:
        documents = self._documents.parse(source)
        if not documents:
            return None
        if len(documents) != 1:
            raise FlowValidationError("Expected one frontmatter block attached to this declaration")
        return self._decoder.parse(documents[0])
