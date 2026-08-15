"""Resolves a path through nested workflow runtime values."""

from __future__ import annotations

from harness.interpolation_error_creating import InterpolationErrorCreating
from harness.nested_component_accessing import NestedComponentAccessing
from harness.nested_value_resolving import NestedValueResolving


"""
solid-name: NestedPathResolver
solid-category: service
solid-spec: [SPEC-037]
solid-description: Resolves each component of a nested workflow reference.
"""
class NestedPathResolver(NestedValueResolving):
    def __init__(
        self,
        component_accessor: NestedComponentAccessing,
        error_factory: InterpolationErrorCreating,
    ) -> None:
        self._component_accessor = component_accessor
        self._error_factory = error_factory

    def resolve(
        self,
        root: object,
        path: list[str],
        reference: str,
    ) -> object:
        current = root
        for component in path:
            resolved = self._component_accessor.access(current, component)
            if not resolved.present:
                raise self._error_factory.create(reference)
            current = resolved.value
        return current
