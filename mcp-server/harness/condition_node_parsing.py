"""Defines parsing for one workflow condition node shape."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from harness.condition_declaration import ConditionDeclaration
from harness.condition_parsing import ConditionParsing


"""
solid-name: ConditionNodeParsing
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for mapping one condition node shape into a typed declaration.
"""
class ConditionNodeParsing(Protocol):
    def parse(
        self,
        raw: Mapping[object, object],
        nested_parser: ConditionParsing,
    ) -> ConditionDeclaration: ...
