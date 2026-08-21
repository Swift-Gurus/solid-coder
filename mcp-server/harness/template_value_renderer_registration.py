"""Defines one typed workflow template-value renderer registration."""

from __future__ import annotations

from dataclasses import dataclass

from harness.template_value_rendering import TemplateValueRendering
from harness.resolved_workflow_context_value import ResolvedWorkflowContextValue


"""
solid-name: TemplateValueRendererRegistration
solid-category: service
solid-spec: [SPEC-037]
solid-description: Associates a runtime workflow-value type with its template renderer.
"""
@dataclass(frozen=True)
class TemplateValueRendererRegistration:
    value_type: type
    renderer: TemplateValueRendering

    def render(
        self,
        value: object,
    ) -> ResolvedWorkflowContextValue[str]:
        if not isinstance(value, self.value_type):
            return ResolvedWorkflowContextValue(present=False)
        return ResolvedWorkflowContextValue(
            present=True,
            value=self.renderer.render(value),
        )
