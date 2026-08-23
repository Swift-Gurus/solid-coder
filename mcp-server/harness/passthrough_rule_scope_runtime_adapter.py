"""Preserves authored runtime controls for an iterated rule scope."""

from harness.rule_scope_runtime_adapting import RuleScopeRuntimeAdapting
from harness.workflow_include_runtime import WorkflowIncludeRuntime


"""
solid-name: PassthroughRuleScopeRuntimeAdapter
solid-category: service
solid-spec: [SPEC-039]
solid-description: Preserves authored include controls for a rule scope that requires no runtime transformation.
"""
class PassthroughRuleScopeRuntimeAdapter(RuleScopeRuntimeAdapting):
    def adapt(
        self,
        runtime: WorkflowIncludeRuntime,
    ) -> WorkflowIncludeRuntime:
        return runtime
