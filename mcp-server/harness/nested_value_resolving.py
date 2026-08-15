"""Defines nested runtime value resolution."""

from __future__ import annotations

from typing import Protocol


"""
solid-name: NestedValueResolving
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for traversing a named path through a runtime value.
"""
class NestedValueResolving(Protocol):
    def resolve(
        self,
        root: object,
        path: list[str],
        reference: str,
    ) -> object: ...
