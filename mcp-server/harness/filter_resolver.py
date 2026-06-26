"""
solid-description: Enables applying named filters to template values.
solid-category: service
"""

from __future__ import annotations

from typing import Any, Callable, Protocol

from harness.interpolation_error import InterpolationError


class FilterResolving(Protocol):
    """
    solid-description: Contract for applying a named filter to a resolved template value.
    solid-category: abstraction
    """

    def apply(self, value: Any, filter_name: str) -> Any: ...


_DEFAULT_FILTERS: dict[str, Callable[[Any], Any]] = {
    "length": len,
}


class FilterResolver:
    """
    solid-description: Applies named filters to template values.
    solid-category: service
    """

    def __init__(self, registry: dict[str, Callable[[Any], Any]] | None = None) -> None:
        self._registry = registry if registry is not None else _DEFAULT_FILTERS

    def apply(self, value: Any, filter_name: str) -> Any:
        fn = self._registry.get(filter_name)
        if fn is None:
            raise InterpolationError(f"Unknown filter: '{filter_name}'")
        return fn(value)
