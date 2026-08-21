"""Renders workflow templates with typed runtime context."""

from __future__ import annotations

import re
from typing import Protocol

from harness.expression_evaluating import ExpressionEvaluating
from harness.workflow_run_context import WorkflowRunContext
from harness.template_value_rendering import TemplateValueRendering


"""
solid-name: TemplateRendering
solid-category: abstraction
solid-spec: [SPEC-030, SPEC-037]
solid-description: Contract for rendering workflow templates against typed runtime context.
"""
class TemplateRendering(Protocol):
    def render(self, template: str, context: WorkflowRunContext) -> str: ...


_EXPR_RE = re.compile(r"\{\{([^}]+)\}\}")


"""
solid-name: Interpolator
solid-category: service
solid-spec: [SPEC-030, SPEC-037]
solid-description: Renders workflow templates by resolving embedded expressions against runtime context.
"""
class Interpolator(TemplateRendering):
    def __init__(
        self,
        evaluator: ExpressionEvaluating,
        value_renderer: TemplateValueRendering,
    ) -> None:
        self._evaluator = evaluator
        self._value_renderer = value_renderer

    def render(self, template: str, context: WorkflowRunContext) -> str:
        def replace(match: re.Match) -> str:
            return self._value_renderer.render(
                self._evaluator.evaluate(match.group(1).strip(), context)
            )

        return _EXPR_RE.sub(replace, template)
