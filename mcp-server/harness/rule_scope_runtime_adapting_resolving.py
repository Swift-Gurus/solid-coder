"""Defines resolution of rule-scope runtime adaptation."""

from typing import Protocol

from harness.rule_scope import RuleScope
from harness.rule_scope_runtime_adapting import RuleScopeRuntimeAdapting


"""
solid-name: RuleScopeRuntimeAdaptingResolving
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for resolving include-runtime adaptation from typed rule execution scope.
"""
class RuleScopeRuntimeAdaptingResolving(Protocol):
    def resolve(
        self,
        scope: RuleScope,
    ) -> RuleScopeRuntimeAdapting: ...
