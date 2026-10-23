from source.analysis.calls.source_call import SourceCall
from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing
from source.source_line_range import SourceLineRange
from tree_sitter import Node

"""
solid-name: TreeSitterSwiftCallParser
solid-category: boundary-adapter
solid-spec: [SPEC-067]
solid-description: Decodes actual Swift invocation syntax and argument labels into source evidence, without inferring callable ownership or following dynamic dispatch.
"""


class TreeSitterSwiftCallParser(SourceSyntaxParsing[Node, SourceCall | None]):
    def __init__(
        self,
        spans: SourceSyntaxParsing[Node, SourceLineRange],
        tokens: SourceSyntaxParsing[Node, list[str]],
    ) -> None:
        self._spans = spans
        self._tokens = tokens

    def parse(self, source: Node) -> SourceCall | None:
        if source.type != "call_expression" or source.has_error or source.is_missing:
            return None
        children = [child for child in source.named_children if not child.is_extra]
        if not children or not children[0].text or not source.text:
            return None
        labels: list[str] = []
        for suffix in children[1:]:
            for arguments in suffix.named_children:
                if arguments.type == "value_arguments":
                    for argument in arguments.named_children:
                        if argument.type == "value_argument":
                            label = argument.child_by_field_name("name")
                            labels.append(
                                label.text.decode("utf-8")
                                if label is not None and label.text
                                else "_"
                            )
                elif arguments.type == "lambda_literal":
                    labels.append("_")
        return SourceCall(
            identity=f"call:{source.start_byte}:{source.end_byte}",
            callee="".join(self._tokens.parse(children[0])),
            argument_labels=labels,
            expression=source.text.decode("utf-8"),
            span=self._spans.parse(source),
            start_offset=source.start_byte,
            end_offset=source.end_byte,
        )
