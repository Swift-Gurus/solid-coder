"""Materializes one catalog rule's include controls and applicability."""

from dataclasses import replace
from typing import Protocol

from harness.condition_conjoining import ConditionConjoining
from harness.flow_validation_error import FlowValidationError
from harness.rule_match_condition_compiling import RuleMatchConditionCompiling
from harness.rule_scope_runtime_adapting_resolving import (
    RuleScopeRuntimeAdaptingResolving,
)
from harness.rule_set_member_include import RuleSetMemberInclude
from harness.workflow_include_runtime import WorkflowIncludeRuntime
from harness.workflow_source import WorkflowSource

"""
solid-name: RuleSetMemberResolving
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for materializing a typed rule-set member from a workflow source and invocation controls.
"""


class RuleSetMemberResolving(Protocol):
    def resolve(
        self, source: WorkflowSource, runtime: WorkflowIncludeRuntime
    ) -> RuleSetMemberInclude: ...


"""
solid-name: RuleSetMemberResolver
solid-category: service
solid-spec: [SPEC-039]
solid-description: Adapts rule scope and compiles applicability against explicit input bindings before composing one include member.
"""


class RuleSetMemberResolver(RuleSetMemberResolving):
    def __init__(
        self,
        match_compiler: RuleMatchConditionCompiling,
        condition_conjoiner: ConditionConjoining,
        runtime_adapters: RuleScopeRuntimeAdaptingResolving,
    ) -> None:
        self._match_compiler = match_compiler
        self._condition_conjoiner = condition_conjoiner
        self._runtime_adapters = runtime_adapters

    def resolve(
        self, source: WorkflowSource, runtime: WorkflowIncludeRuntime
    ) -> RuleSetMemberInclude:
        rule = source.rule
        if rule is None:
            raise FlowValidationError(
                f"Workflow '{source.id}' is not enrolled as a review rule"
            )
        member_runtime = self._runtime_adapters.resolve(rule.scope).adapt(
            replace(runtime, condition=None)
        )
        return RuleSetMemberInclude(
            workflow_id=source.id,
            alias=source.id,
            runtime=member_runtime,
            condition=self._condition_conjoiner.conjoin(
                [
                    runtime.condition,
                    self._match_compiler.compile(
                        rule.match, member_runtime.input_bindings
                    ),
                ]
            ),
        )
