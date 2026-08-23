"""Adapts a fanned-out rule include to one file-scoped execution."""

from dataclasses import replace

from harness.rule_scope_runtime_adapting import RuleScopeRuntimeAdapting
from harness.workflow_include_runtime import WorkflowIncludeRuntime
from harness.workflow_input_bindings_rebinding import (
    WorkflowInputBindingsRebinding,
)


"""
solid-name: FileRuleScopeRuntimeAdapter
solid-category: service
solid-spec: [SPEC-039]
solid-description: Removes unit fan-out and supplies the normalized file expression to a file-scoped rule.
"""
class FileRuleScopeRuntimeAdapter(RuleScopeRuntimeAdapting):
    def __init__(
        self,
        input_bindings: WorkflowInputBindingsRebinding,
    ) -> None:
        self._input_bindings = input_bindings

    def adapt(
        self,
        runtime: WorkflowIncludeRuntime,
    ) -> WorkflowIncludeRuntime:
        if runtime.for_each is None:
            return runtime
        return replace(
            runtime,
            for_each=None,
            input_bindings=self._input_bindings.rebind(
                runtime.input_bindings
            ),
        )
