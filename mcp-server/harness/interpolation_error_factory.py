"""Creates actionable workflow interpolation errors."""

from __future__ import annotations

from harness.interpolation_error import InterpolationError
from harness.interpolation_error_creating import InterpolationErrorCreating


"""
solid-name: InterpolationErrorFactory
solid-category: factory
solid-spec: [SPEC-037]
solid-description: Creates an actionable error for an unresolved workflow reference.
"""
class InterpolationErrorFactory(InterpolationErrorCreating):
    def create(
        self,
        reference: str,
        detail: str | None = None,
    ) -> InterpolationError:
        if detail is not None:
            return InterpolationError(f"Unresolvable reference: {detail}")
        return InterpolationError(f"Unresolvable reference: '{reference}'")
