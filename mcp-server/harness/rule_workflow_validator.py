"""Validates executable review-rule workflow structure."""

from harness.flow_def import FlowDef
from harness.rule_workflow_validating import RuleWorkflowValidating
from harness.rule_workflow_validation_plan_validating import (
    RuleWorkflowValidationPlanValidating,
)
from harness.rule_workflow_validation_planning import (
    RuleWorkflowValidationPlanning,
)


"""
solid-name: RuleWorkflowValidator
solid-category: service
solid-spec: [SPEC-039]
solid-description: Validates rule enrollment, required observation steps, and unique metric identities.
"""
class RuleWorkflowValidator(RuleWorkflowValidating):
    def __init__(
        self,
        planner: RuleWorkflowValidationPlanning,
        plan_validator: RuleWorkflowValidationPlanValidating,
    ) -> None:
        self._planner = planner
        self._plan_validator = plan_validator

    def validate(self, definition: FlowDef) -> None:
        self._plan_validator.validate(self._planner.resolve(definition))
