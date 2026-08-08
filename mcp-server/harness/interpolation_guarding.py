"""
solid-name: InterpolationGuarding
solid-category: abstraction
solid-spec: [SPEC-031]
solid-description: Contract for executing a callable and returning either its result or an error message.
"""

from __future__ import annotations

from typing import Callable, Protocol, TypeVar

_T = TypeVar("_T")


class InterpolationGuarding(Protocol):
    def guard(self, resolve: Callable[[], _T]) -> tuple[_T | None, str | None]: ...
