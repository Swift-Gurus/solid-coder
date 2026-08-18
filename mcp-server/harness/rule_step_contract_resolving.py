"""Defines rule-step boundary contract resolution."""

from typing import Protocol

from harness.rule_step_contract import RuleStepContract


"""
solid-name: RuleStepContractResolving
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for resolving workflow-step boundary values into typed rule-step contracts.
"""
class RuleStepContractResolving(Protocol):
    def resolve(self, raw: dict) -> RuleStepContract: ...
