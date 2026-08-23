"""Composes rule-scope runtime adaptation policies."""

from harness.file_rule_scope_runtime_adapter import (
    FileRuleScopeRuntimeAdapter,
)
from harness.named_workflow_input_bindings_rebinder import (
    NamedWorkflowInputBindingsRebinder,
)
from harness.passthrough_rule_scope_runtime_adapter import (
    PassthroughRuleScopeRuntimeAdapter,
)
from harness.rule_scope import RuleScope
from harness.rule_scope_runtime_adapter_registration import (
    RuleScopeRuntimeAdapterRegistration,
)
from harness.rule_scope_runtime_adapter_resolver import (
    RuleScopeRuntimeAdapterResolver,
)


"""
solid-name: RuleScopeRuntimeAdapterResolverFactory
solid-category: factory
solid-spec: [SPEC-039]
solid-description: Provides registered unit- and file-scope include-runtime adaptation policies.
"""
class RuleScopeRuntimeAdapterResolverFactory:
    def make(self) -> RuleScopeRuntimeAdapterResolver:
        return RuleScopeRuntimeAdapterResolver([
            RuleScopeRuntimeAdapterRegistration(
                scope=RuleScope.UNIT,
                adapter=PassthroughRuleScopeRuntimeAdapter(),
            ),
            RuleScopeRuntimeAdapterRegistration(
                scope=RuleScope.FILE,
                adapter=FileRuleScopeRuntimeAdapter(
                    input_bindings=NamedWorkflowInputBindingsRebinder(
                        source_name="review_file",
                        target_name="review_unit",
                    )
                ),
            ),
        ])
