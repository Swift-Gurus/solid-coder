"""Associates one rule scope with its runtime adaptation capability."""

from dataclasses import dataclass

from harness.rule_scope import RuleScope
from harness.rule_scope_runtime_adapting import RuleScopeRuntimeAdapting


"""
solid-name: RuleScopeRuntimeAdapterRegistration
solid-category: model
solid-spec: [SPEC-039]
solid-description: Associates one typed rule execution scope with its include-runtime adaptation capability.
"""
@dataclass(frozen=True)
class RuleScopeRuntimeAdapterRegistration:
    scope: RuleScope
    adapter: RuleScopeRuntimeAdapting
