"""Defines interpolation error construction."""

from __future__ import annotations

from typing import Protocol

from harness.interpolation_error import InterpolationError


"""
solid-name: InterpolationErrorCreating
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for creating an actionable unresolved-reference error.
"""
class InterpolationErrorCreating(Protocol):
    def create(
        self,
        reference: str,
        detail: str | None = None,
    ) -> InterpolationError: ...
