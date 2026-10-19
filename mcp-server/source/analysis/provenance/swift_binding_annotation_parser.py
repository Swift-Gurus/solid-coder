"""Locates explicit Swift annotations at exact value-declaration offsets."""

from tree_sitter import Node, Tree

from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing


"""
solid-name: SwiftBindingAnnotationParser
solid-category: boundary-adapter
solid-spec: [SPEC-064]
solid-description: Locates the explicit type annotation belonging to a Swift value declaration.
"""
class SwiftBindingAnnotationParser(SourceSyntaxParsing[int, Node | None]):
    def __init__(self, tree: Tree) -> None:
        self._tree = tree

    def parse(self, source: int) -> Node | None:
        declaration = self._tree.root_node.descendant_for_byte_range(source, source)
        while declaration is not None and declaration.type not in {"parameter", "property_declaration"}:
            declaration = declaration.parent
        if declaration is None:
            return None
        if declaration.type == "parameter":
            annotations = [node for node in declaration.children_by_field_name("name") if node.type != "simple_identifier"]
            return annotations[0] if len(annotations) == 1 else None
        children = [node for node in declaration.named_children if not node.is_extra]
        for index, node in enumerate(children[:-1]):
            if node.type == "pattern" and node.start_byte <= source < node.end_byte:
                candidate = children[index + 1]
                return candidate if candidate.type == "type_annotation" else None
        return None
