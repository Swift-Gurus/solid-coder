"""Validates executable review-rule workflow structure."""

from harness.flow_def import FlowDef
from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.rule_match_validating import RuleMatchValidating
from harness.rule_workflow_validating import RuleWorkflowValidating


"""
solid-name: RuleWorkflowValidator
solid-category: service
solid-spec: [SPEC-039]
solid-description: Validates rule enrollment, required observation steps, and unique metric identities.
"""
class RuleWorkflowValidator(RuleWorkflowValidating):
    def __init__(
        self,
        match_validator: RuleMatchValidating,
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._match_validator = match_validator
        self._error_factory = error_factory

    def validate(self, definition: FlowDef) -> None:
        metric_steps = [
            step for step in definition.step_declarations if step.type == "metric"
        ]
        exception_steps = [
            step for step in definition.step_declarations if step.type == "exception"
        ]
        if definition.rule is None:
            if metric_steps or exception_steps:
                raise self._error_factory.create(
                    "Metric and exception steps require a root 'rule' declaration"
                )
            return
        self._match_validator.validate(definition.rule.match)
        if not metric_steps:
            raise self._error_factory.create(
                f"Rule workflow '{definition.workflow_id}' must declare at least one 'metric' step"
            )
        if len(exception_steps) != 1:
            raise self._error_factory.create(
                f"Rule workflow '{definition.workflow_id}' must declare exactly one 'exception' step"
            )

        seen_metric_ids: set[str] = set()
        for step in metric_steps:
            if step.metric is None:
                raise self._error_factory.create(
                    f"Metric step '{step.id}' is missing its typed metric declaration"
                )
            metric_id = step.metric.metric_id
            if metric_id in seen_metric_ids:
                raise self._error_factory.create(
                    f"Rule workflow '{definition.workflow_id}' has duplicate metric_id '{metric_id}'"
                )
            seen_metric_ids.add(metric_id)
