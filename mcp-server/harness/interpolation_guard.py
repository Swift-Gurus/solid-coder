"""
solid-name: InterpolationGuard
solid-category: service
solid-spec: [SPEC-031]
solid-description: Guards callable execution by converting exceptions to error messages.
"""

from __future__ import annotations

from typing import Callable, TypeVar

from harness.interpolation_error import InterpolationError
from harness.interpolation_guarding import InterpolationGuarding

_T = TypeVar("_T")


class InterpolationGuard(InterpolationGuarding):

    def guard(self, resolve: Callable[[], _T]) -> tuple[_T | None, str | None]:
        try:
            return resolve(), None
        except InterpolationError as exc:
            return None, str(exc)
