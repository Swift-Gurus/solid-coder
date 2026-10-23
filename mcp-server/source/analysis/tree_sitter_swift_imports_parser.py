"""Extracts Swift import evidence."""

from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing
from source.source_evidence import SourceEvidence
from source.source_line_range import SourceLineRange
from tree_sitter import Node

"""
solid-name: TreeSitterSwiftImportsParser
solid-category: boundary-adapter
solid-spec: [SPEC-057]
solid-description: Identifies explicitly imported Swift modules with source line evidence.
"""


class TreeSitterSwiftImportsParser(SourceSyntaxParsing[Node, list[SourceEvidence]]):
    def __init__(self, spans: SourceSyntaxParsing[Node, SourceLineRange]) -> None:
        self._spans = spans

    def parse(self, source: Node) -> list[SourceEvidence]:
        imports: list[SourceEvidence] = []
        for declaration in source.named_children:
            if declaration.type != "import_declaration":
                continue
            module = next(
                (
                    child
                    for child in declaration.named_children
                    if child.type == "identifier"
                ),
                None,
            )
            if module is not None and module.text:
                imports.append(
                    SourceEvidence(
                        fact=module.text.decode("utf-8"),
                        span=self._spans.parse(declaration),
                    )
                )
        return imports
