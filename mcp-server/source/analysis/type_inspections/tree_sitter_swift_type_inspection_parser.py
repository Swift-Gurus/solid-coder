"""Decodes Swift type-inspection expressions and patterns into syntax facts."""

from tree_sitter import Node

from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing
from source.analysis.type_inspections.source_type_inspection import SourceTypeInspection
from source.analysis.type_inspections.source_type_inspection_kind import SourceTypeInspectionKind
from source.source_byte_range import SourceByteRange
from source.source_line_range import SourceLineRange


"""
solid-name: TreeSitterSwiftTypeInspectionParser
solid-category: boundary-adapter
solid-spec: [SPEC-063]
solid-description: Decodes Swift cast, type-test and runtime-type-query syntax, including pattern matching, for auditable source inspection without semantic ownership inference.
"""
class TreeSitterSwiftTypeInspectionParser(SourceSyntaxParsing[Node, SourceTypeInspection | None]):
    def __init__(
        self,
        spans: SourceSyntaxParsing[Node, SourceLineRange],
        tokens: SourceSyntaxParsing[Node, list[str]],
    ) -> None:
        self._spans = spans
        self._tokens = tokens

    def parse(self, source: Node) -> SourceTypeInspection | None:
        if source.has_error or source.is_missing:
            return None
        target_tokens: list[str] = []
        target: Node | None = None
        match source.type:
            case "as" | "is":
                return self._pattern_inspection(source)
            case "as_expression":
                operator = next((child for child in source.named_children if child.type == "as_operator"), None)
                if operator is None:
                    return None
                match self._tokens.parse(operator):
                    case ["as?"]:
                        kind = SourceTypeInspectionKind.CONDITIONAL_CAST
                    case ["as!"]:
                        kind = SourceTypeInspectionKind.FORCED_CAST
                    case ["as"]:
                        kind = SourceTypeInspectionKind.CONVERSION
                    case _:
                        return None
                operand = source.child_by_field_name("expr")
                target = source.child_by_field_name("name")
                if target is None:
                    return None
                target_tokens = self._tokens.parse(target)
            case "check_expression":
                kind = SourceTypeInspectionKind.TYPE_TEST
                operand = source.child_by_field_name("target")
                target = source.child_by_field_name("name")
                if target is None:
                    return None
                target_tokens = self._tokens.parse(target)
            case "call_expression":
                kind = SourceTypeInspectionKind.TYPE_QUERY
                operand = self._query_operand(source)
            case _:
                return None
        if operand is None or not operand.text or not source.text:
            return None
        return SourceTypeInspection(
            identity=f"type-inspection:{source.start_byte}:{source.end_byte}",
            kind=kind,
            expression=source.text.decode("utf-8"),
            operand=operand.text.decode("utf-8"),
            target_tokens=target_tokens,
            span=self._spans.parse(source),
            start_offset=source.start_byte,
            end_offset=source.end_byte,
            operand_range=SourceByteRange(start=operand.start_byte, end=operand.end_byte),
            destination_range=SourceByteRange(start=target.start_byte, end=target.end_byte) if target is not None else None,
        )

    def _pattern_inspection(self, operator: Node) -> SourceTypeInspection | None:
        parent = operator.parent
        if parent is None or parent.type not in {
            "pattern", "if_statement", "guard_statement", "while_statement",
        }:
            return None
        target = operator.next_named_sibling
        while target is not None and target.is_extra:
            target = target.next_named_sibling
        if (
            target is None or target.is_missing or target.has_error
            or not target.text or target not in parent.children_by_field_name("name")
            or not parent.text
        ):
            return None
        start = operator.start_byte
        end = target.end_byte
        return SourceTypeInspection(
            identity=f"type-inspection:{start}:{end}",
            kind=(
                SourceTypeInspectionKind.PATTERN_CAST
                if operator.type == "as" else SourceTypeInspectionKind.PATTERN_TYPE_TEST
            ),
            expression=parent.text[start - parent.start_byte:end - parent.start_byte].decode("utf-8"),
            operand=None,
            target_tokens=self._tokens.parse(target),
            span=SourceLineRange(
                start=self._spans.parse(operator).start,
                end=self._spans.parse(target).end,
            ),
            start_offset=start,
            end_offset=end,
            destination_range=SourceByteRange(start=target.start_byte, end=target.end_byte),
        )

    def _query_operand(self, source: Node) -> Node | None:
        children = [child for child in source.named_children if not child.is_extra]
        if len(children) != 2 or self._tokens.parse(children[0]) not in [["type"], ["Swift", ".", "type"]]:
            return None
        arguments = [child for child in children[1].named_children if not child.is_extra]
        if len(arguments) != 1 or arguments[0].type != "value_arguments":
            return None
        values = [child for child in arguments[0].named_children if not child.is_extra]
        if len(values) != 1 or values[0].type != "value_argument":
            return None
        label = values[0].child_by_field_name("name")
        if label is None or self._tokens.parse(label) != ["of"]:
            return None
        return values[0].child_by_field_name("value")
