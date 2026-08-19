"""Coordinates validation of an ownership-partitioned rule plan."""

from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.rule_workflow_validation_plan import RuleWorkflowValidationPlan
from harness.rule_workflow_validation_plan_validating import (
    RuleWorkflowValidationPlanValidating,
)
from harness.rule_workflow_validation_scope_validating import (
    RuleWorkflowValidationScopeValidating,
)


"""
solid-name: RuleWorkflowValidationPlanValidator
solid-category: service
solid-spec: [SPEC-039]
solid-description: Rejects unowned rule steps and delegates each typed ownership scope to rule-structure validation.
"""
class RuleWorkflowValidationPlanValidator(RuleWorkflowValidationPlanValidating):
    def __init__(
        self,
        scope_validator: RuleWorkflowValidationScopeValidating,
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._scope_validator = scope_validator
        self._error_factory = error_factory

    def validate(self, plan: RuleWorkflowValidationPlan) -> None:
        if plan.unowned_steps:
            raise self._error_factory.create(
                "Metric and exception steps require an owning rule declaration"
            )
        for scope in plan.scopes:
            self._scope_validator.validate(scope)
