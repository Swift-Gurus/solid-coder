"""Defines structural validation of one owned rule workflow scope."""

from typing import Protocol

from harness.rule_workflow_validation_scope import RuleWorkflowValidationScope


"""
solid-name: RuleWorkflowValidationScopeValidating
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for validating one rule declaration against only the workflow steps it owns.
"""
class RuleWorkflowValidationScopeValidating(Protocol):
    def validate(self, scope: RuleWorkflowValidationScope) -> None: ...
