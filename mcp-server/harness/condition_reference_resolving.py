"""Defines condition reference resolution."""

from __future__ import annotations

from typing import Protocol

from harness.resolved_condition_value import ResolvedConditionValue
from harness.workflow_expression import WorkflowExpression
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: ConditionReferenceResolving
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for resolving workflow condition references with presence information.
"""
class ConditionReferenceResolving(Protocol):
    def resolve(
        self,
        reference: WorkflowExpression,
        context: WorkflowRunContext,
    ) -> ResolvedConditionValue: ...
