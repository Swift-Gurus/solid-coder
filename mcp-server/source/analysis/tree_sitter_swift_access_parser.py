"""Reads declaration access at the Swift syntax boundary."""

from tree_sitter import Node

from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing
from source.members.source_member_visibility import SourceMemberVisibility


"""
solid-name: TreeSitterSwiftAccessParser
solid-category: boundary-adapter
solid-spec: [SPEC-057, SPEC-062]
solid-description: Reads explicit Swift declaration access while excluding setter-only restrictions.
"""
class TreeSitterSwiftAccessParser(SourceSyntaxParsing[Node, SourceMemberVisibility | None]):
    def parse(self, source: Node) -> SourceMemberVisibility | None:
        for modifiers in source.named_children:
            if modifiers.type != "modifiers":
                continue
            for modifier in modifiers.named_children:
                if modifier.type != "visibility_modifier":
                    continue
                for access in SourceMemberVisibility:
                    if modifier.text == access.value.encode("utf-8"):
                        return access
        return None
