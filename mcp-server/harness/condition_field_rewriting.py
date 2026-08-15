"""Defines condition-field rewriting for durable workflow snapshots."""

from __future__ import annotations

from typing import Protocol

from harness.condition_declaration import ConditionDeclaration


"""
solid-name: ConditionFieldRewriting
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for rewriting typed conditions into durable workflow snapshot fields.
"""
class ConditionFieldRewriting(Protocol):
    def rewrite(
        self,
        target: dict[str, object],
        condition: ConditionDeclaration | None,
    ) -> None: ...
