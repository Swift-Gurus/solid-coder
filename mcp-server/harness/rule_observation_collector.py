"""Collects typed observations from completed executable rule steps."""

from harness.completed_step_outputs_resolving import CompletedStepOutputsResolving
from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.rule_execution_instance import RuleExecutionInstance
from harness.rule_assessment_observations_decoding import (
    RuleAssessmentObservationsDecoding,
)
from harness.rule_exception_decision import RuleExceptionDecision
from harness.rule_metric_observation import RuleMetricObservation
from harness.rule_observation_collecting import RuleObservationCollecting
from harness.rule_observations import RuleObservations
from harness.run_state import RunState


"""
solid-name: RuleObservationCollector
solid-category: service
solid-spec: [SPEC-039]
solid-description: Collects validated observations for one executable review rule.
"""
class RuleObservationCollector(RuleObservationCollecting):
    def __init__(
        self,
        outputs_resolver: CompletedStepOutputsResolving,
        assessment_decoder: RuleAssessmentObservationsDecoding,
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._outputs_resolver = outputs_resolver
        self._assessment_decoder = assessment_decoder
        self._error_factory = error_factory

    def collect(
        self,
        instance: RuleExecutionInstance,
        run_state: RunState,
    ) -> RuleObservations:
        assessment_step = next(
            (
                step
                for step in instance.steps
                if step.assessment is not None
            ),
            None,
        )
        if assessment_step is not None and assessment_step.assessment is not None:
            return self._assessment_decoder.decode(
                assessment_step.assessment,
                self._outputs_resolver.resolve(assessment_step.id, run_state),
            )

        metrics: list[RuleMetricObservation] = []
        exception: RuleExceptionDecision | None = None

        for step in instance.steps:
            if step.metric is not None:
                outputs = self._outputs_resolver.resolve(step.id, run_state)
                metrics.append(
                    RuleMetricObservation.model_validate(
                        {
                            "declaration": step.metric,
                            "value": outputs.get("value"),
                            "additional_info": outputs.get("additional_info"),
                        }
                    )
                )
            elif step.type == "exception":
                outputs = self._outputs_resolver.resolve(step.id, run_state)
                exception = RuleExceptionDecision.model_validate(
                    {
                        "is_exception": outputs.get("is_exception"),
                        "additional_info": outputs.get("additional_info"),
                    }
                )

        if exception is None:
            raise self._error_factory.create(
                f"Rule workflow '{instance.workflow.workflow_id}' has no completed exception observation"
            )
        return RuleObservations(metrics=metrics, exception=exception)
