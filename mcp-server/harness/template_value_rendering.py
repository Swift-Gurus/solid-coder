"""Defines rendering of resolved workflow template values."""

from __future__ import annotations

from typing import Protocol, TypeVar

ValueT = TypeVar("ValueT", contravariant=True)


"""
solid-name: TemplateValueRendering
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for rendering a typed value into message or workflow template text.
"""
class TemplateValueRendering(Protocol[ValueT]):
    def render(self, value: ValueT) -> str: ...
