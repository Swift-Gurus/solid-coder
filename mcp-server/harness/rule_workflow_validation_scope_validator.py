"""Validates the structure of one owned review-rule workflow."""

from harness.rule_match_validating import RuleMatchValidating
from harness.rule_metric_identity_validating import RuleMetricIdentityValidating
from harness.rule_workflow_structure_validating import (
    RuleWorkflowStructureValidating,
)
from harness.rule_workflow_validation_scope import RuleWorkflowValidationScope
from harness.rule_workflow_validation_scope_validating import (
    RuleWorkflowValidationScopeValidating,
)


"""
solid-name: RuleWorkflowValidationScopeValidator
solid-category: service
solid-spec: [SPEC-039]
solid-description: Validates matcher, metric, exception, and metric-identity requirements for one owned rule workflow.
"""
class RuleWorkflowValidationScopeValidator(
    RuleWorkflowValidationScopeValidating
):
    def __init__(
        self,
        match_validator: RuleMatchValidating,
        structure_validator: RuleWorkflowStructureValidating,
        metric_identity_validator: RuleMetricIdentityValidating,
    ) -> None:
        self._match_validator = match_validator
        self._structure_validator = structure_validator
        self._metric_identity_validator = metric_identity_validator

    def validate(self, scope: RuleWorkflowValidationScope) -> None:
        self._match_validator.validate(scope.declaration.match)
        metrics = self._structure_validator.validate(scope)
        self._metric_identity_validator.validate(
            scope.workflow_id,
            metrics,
        )
