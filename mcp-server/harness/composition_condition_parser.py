"""Parses composed workflow condition declarations."""

from __future__ import annotations

from collections.abc import Mapping

from harness.all_condition import AllCondition
from harness.any_condition import AnyCondition
from harness.condition_declaration import ConditionDeclaration
from harness.condition_node_parsing import ConditionNodeParsing
from harness.condition_parsing import ConditionParsing
from harness.models import FlowValidationError
from harness.not_condition import NotCondition


"""
solid-name: CompositionConditionParser
solid-category: boundary
solid-spec: [SPEC-037]
solid-description: Maps composed condition input into typed condition declarations.
"""
class CompositionConditionParser(ConditionNodeParsing):
    _COMPOSITIONS = frozenset({"all", "any", "not"})

    def parse(
        self,
        raw: Mapping[object, object],
        nested_parser: ConditionParsing,
    ) -> ConditionDeclaration:
        composition_keys = self._COMPOSITIONS.intersection(raw.keys())
        if len(composition_keys) != 1 or len(raw) != 1:
            raise FlowValidationError("Workflow condition has unsupported condition fields")
        composition = next(iter(composition_keys))
        value = raw[composition]
        if composition == "not":
            return NotCondition(condition=nested_parser.parse(value))
        if not isinstance(value, list) or not value:
            raise FlowValidationError(
                f"Workflow condition '{composition}' must use a non-empty condition list"
            )
        conditions = tuple(nested_parser.parse(candidate) for candidate in value)
        if composition == "all":
            return AllCondition(conditions=conditions)
        return AnyCondition(conditions=conditions)
