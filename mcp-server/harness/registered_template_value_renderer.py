"""Dispatches workflow template values to registered renderers."""

from __future__ import annotations

from harness.template_value_renderer_registration import (
    TemplateValueRendererRegistration,
)
from harness.template_value_rendering import TemplateValueRendering


"""
solid-name: RegisteredTemplateValueRenderer
solid-category: service
solid-spec: [SPEC-037]
solid-description: Dispatches workflow expression values through extensible template-renderer registrations.
"""
class RegisteredTemplateValueRenderer(TemplateValueRendering):

    def __init__(
        self,
        registrations: list[TemplateValueRendererRegistration],
        default_renderer: TemplateValueRendering,
    ) -> None:
        self._registrations = registrations
        self._default_renderer = default_renderer

    def render(self, value: object) -> str:
        for registration in self._registrations:
            rendered = registration.render(value)
            if rendered.present and rendered.value is not None:
                return rendered.value
        return self._default_renderer.render(value)
