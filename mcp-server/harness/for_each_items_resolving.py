"""Defines resolution of workflow iteration items."""

from __future__ import annotations

from typing import Any, Protocol


"""
solid-name: ForEachItemsResolving
solid-category: abstraction
solid-spec: [SPEC-010, SPEC-030]
solid-description: Contract for resolving a workflow for-each expression into an ordered item collection.
"""
class ForEachItemsResolving(Protocol):
    def resolve(
        self,
        step_id: str,
        expression: str,
        context: dict[str, Any],
    ) -> list[Any]: ...
