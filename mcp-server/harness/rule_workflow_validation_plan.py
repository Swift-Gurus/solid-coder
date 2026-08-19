"""Defines the owned and unowned rule steps found in one workflow definition."""

from dataclasses import dataclass, field

from harness.rule_workflow_validation_scope import RuleWorkflowValidationScope
from harness.step_declaration import StepDeclaration


"""
solid-name: RuleWorkflowValidationPlan
solid-category: model
solid-spec: [SPEC-039]
solid-description: Carries ordered rule-validation scopes and any metric or exception steps without rule ownership.
"""
@dataclass(frozen=True)
class RuleWorkflowValidationPlan:
    scopes: list[RuleWorkflowValidationScope] = field(default_factory=list)
    unowned_steps: list[StepDeclaration] = field(default_factory=list)
