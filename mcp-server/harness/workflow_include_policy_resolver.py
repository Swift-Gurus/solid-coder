"""Resolves authored include policy against its enclosing runtime policy."""

from dataclasses import replace
from typing import Protocol

from harness.workflow_include_runtime import WorkflowIncludeRuntime

"""
solid-name: WorkflowIncludePolicyResolving
solid-category: abstraction
solid-spec: [SPEC-067]
solid-description: Contract for resolving omitted execution and presentation settings from enclosing workflow policy.
"""


class WorkflowIncludePolicyResolving(Protocol):
    def resolve(
        self, child: WorkflowIncludeRuntime, parent: WorkflowIncludeRuntime
    ) -> WorkflowIncludeRuntime: ...


"""
solid-name: WorkflowIncludePolicyResolver
solid-category: service
solid-spec: [SPEC-067]
solid-description: Resolves effective workflow execution and presentation modes while preserving explicit local overrides.
"""


class WorkflowIncludePolicyResolver:
    def resolve(
        self, child: WorkflowIncludeRuntime, parent: WorkflowIncludeRuntime
    ) -> WorkflowIncludeRuntime:
        return replace(
            child,
            execution=child.execution if child.execution_declared else parent.execution,
            presentation=child.presentation
            if child.presentation_declared
            else parent.presentation,
        )
