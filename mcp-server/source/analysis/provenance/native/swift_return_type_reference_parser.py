"""Reads compiler-authored semantic references, not hover prose or type names."""

from xml.etree.ElementTree import ParseError, fromstring

from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing


"""
solid-name: SwiftReturnTypeReferenceParser
solid-category: boundary-adapter
solid-spec: [SPEC-064]
solid-description: Extracts an unambiguous semantic return-type identity from structured compiler annotations, preserving unsupported composite contracts as unresolved.
"""
class SwiftReturnTypeReferenceParser(SourceSyntaxParsing[str, str | None]):
    def parse(self, source: str) -> str | None:
        try:
            declaration = fromstring(source)
        except ParseError:
            return None
        returns = list(declaration.iter("decl.function.returntype"))
        if len(returns) != 1:
            return None
        result = returns[0]
        if len(result) != 1 or (result.text or "").strip() not in {"", "any"}:
            return None
        reference = result[0]
        if reference.tag not in {"ref.class", "ref.struct", "ref.protocol", "ref.enum", "ref.typealias"}:
            return None
        if len(reference) or (reference.tail or "").strip() not in {"", "?", "!"}:
            return None
        return reference.get("usr") or None
