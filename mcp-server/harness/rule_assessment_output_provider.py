"""Generates audited outputs for one aggregate rule assessment."""

from harness.output_spec import OutputSpec
from harness.rule_additional_info_output_providing import (
    RuleAdditionalInfoOutputProviding,
)
from harness.rule_assessment_declaration import RuleAssessmentDeclaration
from harness.rule_assessment_output_providing import (
    RuleAssessmentOutputProviding,
)


"""
solid-name: RuleAssessmentOutputProvider
solid-category: boundary
solid-spec: [SPEC-044]
solid-description: Renders typed aggregate metric and exception declarations as JSON-schema workflow outputs.
"""
class RuleAssessmentOutputProvider(RuleAssessmentOutputProviding):
    def __init__(
        self,
        additional_info: RuleAdditionalInfoOutputProviding,
    ) -> None:
        self._additional_info = additional_info

    def provide(
        self,
        assessment: RuleAssessmentDeclaration,
    ) -> list[OutputSpec]:
        additional_info_schema = self._additional_info.provide().schema
        supporting_outputs = [
            OutputSpec(
                name=output.name,
                type=output.type,
                schema=output.schema_value,
                schema_file=output.schema_file,
            )
            for output in assessment.supporting_outputs
        ]
        metric_outputs = [
            OutputSpec(
                name=metric.observation_id,
                type="data",
                schema={
                    "type": "object",
                    "properties": {
                        "value": metric.value.model_dump(
                            mode="json",
                            exclude_none=True,
                        ),
                        "additional_info": additional_info_schema,
                    },
                    "required": ["value", "additional_info"],
                    "additionalProperties": False,
                },
            )
            for metric in assessment.metrics
        ]
        return [
            *supporting_outputs,
            *metric_outputs,
            OutputSpec(
                name=assessment.exception_observation_id,
                type="data",
                schema={
                    "type": "object",
                    "properties": {
                        "is_exception": {"type": "boolean"},
                        "additional_info": additional_info_schema,
                    },
                    "required": ["is_exception", "additional_info"],
                    "additionalProperties": False,
                },
            ),
        ]
