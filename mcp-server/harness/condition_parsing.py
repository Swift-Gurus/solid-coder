"""Defines workflow condition parsing."""

from __future__ import annotations

from typing import Protocol

from harness.condition_declaration import ConditionDeclaration


"""
solid-name: ConditionParsing
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for mapping declarative condition input into a typed condition.
"""
class ConditionParsing(Protocol):
    def parse(self, raw: object) -> ConditionDeclaration: ...
