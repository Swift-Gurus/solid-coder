"""Resolves registered runtime adaptation for a rule scope."""

from harness.flow_validation_error import FlowValidationError
from harness.rule_scope import RuleScope
from harness.rule_scope_runtime_adapter_registration import (
    RuleScopeRuntimeAdapterRegistration,
)
from harness.rule_scope_runtime_adapting import RuleScopeRuntimeAdapting
from harness.rule_scope_runtime_adapting_resolving import (
    RuleScopeRuntimeAdaptingResolving,
)


"""
solid-name: RuleScopeRuntimeAdapterResolver
solid-category: service
solid-spec: [SPEC-039]
solid-description: Resolves registered include-runtime adaptation without hardcoded rule-scope branches.
"""
class RuleScopeRuntimeAdapterResolver(
    RuleScopeRuntimeAdaptingResolving
):
    def __init__(
        self,
        registrations: list[RuleScopeRuntimeAdapterRegistration],
    ) -> None:
        self._registrations = registrations

    def resolve(
        self,
        scope: RuleScope,
    ) -> RuleScopeRuntimeAdapting:
        for registration in self._registrations:
            if registration.scope is scope:
                return registration.adapter
        raise FlowValidationError(
            f"No runtime adapter for rule scope '{scope.value}'"
        )
