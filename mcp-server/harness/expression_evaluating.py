"""Defines workflow expression evaluation."""

from __future__ import annotations

from typing import Any, Protocol

from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: ExpressionEvaluating
solid-category: abstraction
solid-spec: [SPEC-030, SPEC-037]
solid-description: Contract for evaluating one workflow expression against typed runtime context.
"""
class ExpressionEvaluating(Protocol):
    def evaluate(self, expr: str, context: WorkflowRunContext) -> Any: ...
