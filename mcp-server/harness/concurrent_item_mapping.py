"""Defines bounded concurrent mapping over ordered items."""

from __future__ import annotations

from typing import Callable, Protocol, TypeVar


Input = TypeVar("Input")
Output = TypeVar("Output")


"""
solid-name: ConcurrentItemMapping
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for applying one operation concurrently to ordered items within a worker bound.
"""
class ConcurrentItemMapping(Protocol):
    def map(
        self,
        operation: Callable[[Input], Output],
        items: list[Input],
        max_workers: int,
    ) -> list[Output]: ...
