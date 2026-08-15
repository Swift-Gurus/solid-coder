"""Parses workflow condition YAML into typed declarations."""

from __future__ import annotations

from collections.abc import Mapping

from harness.condition_declaration import ConditionDeclaration
from harness.condition_node_parsing import ConditionNodeParsing
from harness.condition_parsing import ConditionParsing
from harness.models import FlowValidationError


"""
solid-name: ConditionParser
solid-category: boundary
solid-spec: [SPEC-037]
solid-description: Maps declarative workflow condition input into validated typed condition models.
"""
class ConditionParser(ConditionParsing):
    _COMPOSITIONS = frozenset({"all", "any", "not"})

    def __init__(
        self,
        composition_parser: ConditionNodeParsing,
        comparison_parser: ConditionNodeParsing,
    ) -> None:
        self._composition_parser = composition_parser
        self._comparison_parser = comparison_parser

    def parse(self, raw: object) -> ConditionDeclaration:
        if not isinstance(raw, Mapping):
            raise FlowValidationError("Workflow condition must be an object")
        parser = (
            self._composition_parser
            if self._COMPOSITIONS.intersection(raw.keys())
            else self._comparison_parser
        )
        return parser.parse(raw, self)
