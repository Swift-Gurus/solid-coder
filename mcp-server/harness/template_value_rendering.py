"""Defines rendering of resolved workflow template values."""

from __future__ import annotations

from typing import Protocol, TypeVar

ValueT_contra = TypeVar("ValueT_contra", contravariant=True)


"""
solid-name: TemplateValueRendering
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for rendering a typed value into message or workflow template text.
"""


class TemplateValueRendering(Protocol[ValueT_contra]):
    def render(self, value: ValueT_contra) -> str: ...
