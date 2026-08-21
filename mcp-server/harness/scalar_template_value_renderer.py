"""Renders ordinary workflow template values."""

from __future__ import annotations

from harness.template_value_rendering import TemplateValueRendering


"""
solid-name: ScalarTemplateValueRenderer
solid-category: boundary
solid-spec: [SPEC-030, SPEC-037]
solid-description: Renders ordinary workflow expression values as template text.
"""
class ScalarTemplateValueRenderer(TemplateValueRendering):
    def render(self, value: object) -> str:
        return str(value)
