"""Validates the supported execution shapes of one review rule."""

from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.metric_declaration import MetricDeclaration
from harness.rule_workflow_structure_validating import (
    RuleWorkflowStructureValidating,
)
from harness.rule_workflow_validation_scope import RuleWorkflowValidationScope


"""
solid-name: RuleWorkflowStructureValidator
solid-category: service
solid-spec: [SPEC-039, SPEC-044]
solid-description: Validates granular or aggregate rule-step structure and returns the declarations that require identity validation.
"""
class RuleWorkflowStructureValidator(RuleWorkflowStructureValidating):
    def __init__(self, error_factory: FlowValidationErrorCreating) -> None:
        self._error_factory = error_factory

    def validate(
        self,
        scope: RuleWorkflowValidationScope,
    ) -> list[MetricDeclaration]:
        metric_steps = [step for step in scope.steps if step.type == "metric"]
        exception_steps = [
            step for step in scope.steps if step.type == "exception"
        ]
        assessment_steps = [
            step for step in scope.steps if step.assessment is not None
        ]
        if assessment_steps:
            if len(assessment_steps) != 1:
                raise self._error_factory.create(
                    f"Rule workflow '{scope.workflow_id}' must declare exactly "
                    "one aggregate assessment step"
                )
            if metric_steps or exception_steps:
                raise self._error_factory.create(
                    f"Rule workflow '{scope.workflow_id}' must not mix an "
                    "aggregate assessment with granular metric or exception steps"
                )
            assessment = assessment_steps[0].assessment
            return assessment.metrics if assessment is not None else []

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
        return [
            step.metric
            for step in metric_steps
            if step.metric is not None
        ]
