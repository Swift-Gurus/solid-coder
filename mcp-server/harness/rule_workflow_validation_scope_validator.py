"""Validates the structure of one owned review-rule workflow."""

from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.rule_match_validating import RuleMatchValidating
from harness.rule_workflow_validation_scope import RuleWorkflowValidationScope
from harness.rule_workflow_validation_scope_validating import (
    RuleWorkflowValidationScopeValidating,
)
from harness.unique_string_validating import UniqueStringValidating


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
        identity_validator: UniqueStringValidating,
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._match_validator = match_validator
        self._identity_validator = identity_validator
        self._error_factory = error_factory

    def validate(self, scope: RuleWorkflowValidationScope) -> None:
        self._match_validator.validate(scope.declaration.match)
        metric_steps = [step for step in scope.steps if step.type == "metric"]
        exception_steps = [
            step for step in scope.steps if step.type == "exception"
        ]
        if not metric_steps:
            raise self._error_factory.create(
                f"Rule workflow '{scope.workflow_id}' must declare at least one 'metric' step"
            )
        if len(exception_steps) != 1:
            raise self._error_factory.create(
                f"Rule workflow '{scope.workflow_id}' must declare exactly one 'exception' step"
            )

        missing_declaration = next(
            (step for step in metric_steps if step.metric is None),
            None,
        )
        if missing_declaration is not None:
            raise self._error_factory.create(
                f"Metric step '{missing_declaration.id}' is missing its typed metric declaration"
            )
        self._identity_validator.validate(
            [
                step.metric.metric_id
                for step in metric_steps
                if step.metric is not None
            ],
            f"metric_id in rule workflow {scope.workflow_id}",
        )
