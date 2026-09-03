"""Decodes one aggregate assessment into existing rule observations."""

from harness.rule_assessment_declaration import RuleAssessmentDeclaration
from harness.rule_assessment_observations_decoding import (
    RuleAssessmentObservationsDecoding,
)
from harness.rule_exception_decision import RuleExceptionDecision
from harness.rule_metric_observation import RuleMetricObservation
from harness.rule_metric_submission import RuleMetricSubmission
from harness.rule_observations import RuleObservations
from harness.step_outputs import StepOutputs
from harness.structured_model_decoding import StructuredModelDecoding


"""
solid-name: RuleAssessmentObservationsDecoder
solid-category: boundary-adapter
solid-spec: [SPEC-044]
solid-description: Maps schema-validated aggregate output values into the established metric and exception observation models.
"""
class RuleAssessmentObservationsDecoder(RuleAssessmentObservationsDecoding):
    def __init__(
        self,
        metric_submission_decoder: StructuredModelDecoding[RuleMetricSubmission],
        exception_decoder: StructuredModelDecoding[RuleExceptionDecision],
    ) -> None:
        self._metric_submission_decoder = metric_submission_decoder
        self._exception_decoder = exception_decoder

    def decode(
        self,
        assessment: RuleAssessmentDeclaration,
        outputs: StepOutputs,
    ) -> RuleObservations:
        metrics: list[RuleMetricObservation] = []
        for declaration in assessment.metrics:
            submission = self._metric_submission_decoder.decode(
                outputs.get(declaration.observation_id),
                f"aggregate metric observation '{declaration.observation_id}'",
            )
            metrics.append(
                RuleMetricObservation(
                    declaration=declaration,
                    value=submission.value,
                    additional_info=submission.additional_info,
                )
            )
        return RuleObservations(
            metrics=metrics,
            exception=self._exception_decoder.decode(
                outputs.get(assessment.exception_observation_id),
                f"aggregate exception observation "
                f"'{assessment.exception_observation_id}'",
            ),
        )
