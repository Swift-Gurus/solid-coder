from tree_sitter import Node

from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing


"""
solid-name: TreeSitterSwiftAccessorsParser
solid-category: boundary-adapter
solid-spec: [SPEC-057]
solid-description: Extracts getter and setter capabilities from stored properties, computed properties, and subscripts while retaining accessor effects.
"""
class TreeSitterSwiftAccessorsParser(SourceSyntaxParsing[Node, list[str]]):
    def __init__(self, tokens: SourceSyntaxParsing[Node, list[str]]) -> None:
        self._tokens = tokens

    def parse(self, source: Node) -> list[str]:
        body = next((
            node for node in source.named_children
            if node.type in {"protocol_property_requirements", "computed_property"}
        ), None)
        if body is None:
            bindings = [
                child for node in [source, *source.children_by_field_name("name")]
                for child in node.named_children if child.type == "value_binding_pattern"
            ]
            if not bindings:
                return []
            mutable = any("var" in self._tokens.parse(node) for node in bindings)
            return ["get", "set"] if mutable else ["get"]
        specifiers = [
            child for node in body.named_children for child in [node, *node.named_children]
            if child.type in {"getter_specifier", "setter_specifier"}
        ]
        if specifiers:
            return [token for node in specifiers for token in self._tokens.parse(node)]
        if any(node.type == "statements" for node in body.named_children):
            return ["get"]
        return []
