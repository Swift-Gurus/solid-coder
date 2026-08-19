"""Defines conjunction of optional workflow conditions."""

from __future__ import annotations

from typing import Protocol

from harness.condition_declaration import ConditionDeclaration


"""
solid-name: ConditionConjoining
solid-category: abstraction
solid-spec: [SPEC-037, SPEC-039]
solid-description: Contract for combining present workflow conditions into one conjunction.
"""
class ConditionConjoining(Protocol):
    def conjoin(
        self,
        conditions: list[ConditionDeclaration | None],
    ) -> ConditionDeclaration | None: ...
