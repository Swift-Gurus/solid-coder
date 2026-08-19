"""Defines planning of owned rule-validation scopes."""

from typing import Protocol

from harness.flow_def import FlowDef
from harness.rule_workflow_validation_plan import RuleWorkflowValidationPlan


"""
solid-name: RuleWorkflowValidationPlanning
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for partitioning one resolved workflow into typed rule-ownership validation scopes.
"""
class RuleWorkflowValidationPlanning(Protocol):
    def resolve(self, definition: FlowDef) -> RuleWorkflowValidationPlan: ...
