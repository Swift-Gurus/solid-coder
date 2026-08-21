"""Defines rendering of resolved workflow template values."""

from __future__ import annotations

from typing import Protocol


"""
solid-name: TemplateValueRendering
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for rendering one resolved workflow expression value into template text.
"""
class TemplateValueRendering(Protocol):
    def render(self, value: object) -> str: ...
