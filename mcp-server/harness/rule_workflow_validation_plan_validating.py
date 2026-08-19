"""Defines structural validation of an ownership-partitioned rule plan."""

from typing import Protocol

from harness.rule_workflow_validation_plan import RuleWorkflowValidationPlan


"""
solid-name: RuleWorkflowValidationPlanValidating
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for validating rule step structure after workflow ownership has been resolved.
"""
class RuleWorkflowValidationPlanValidating(Protocol):
    def validate(self, plan: RuleWorkflowValidationPlan) -> None: ...
