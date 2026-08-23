"""Defines runtime adaptation for one rule execution scope."""

from typing import Protocol

from harness.workflow_include_runtime import WorkflowIncludeRuntime


"""
solid-name: RuleScopeRuntimeAdapting
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for adapting authored include controls to one rule execution scope.
"""
class RuleScopeRuntimeAdapting(Protocol):
    def adapt(
        self,
        runtime: WorkflowIncludeRuntime,
    ) -> WorkflowIncludeRuntime: ...
