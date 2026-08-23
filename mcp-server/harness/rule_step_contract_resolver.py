"""Resolves typed metric metadata and generated rule-step output contracts."""

from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.metric_declaration_decoding import MetricDeclarationDecoding
from harness.output_spec import OutputSpec
from harness.rule_additional_info_output_providing import (
    RuleAdditionalInfoOutputProviding,
)
from harness.rule_step_contract import RuleStepContract
from harness.rule_step_contract_resolving import RuleStepContractResolving


"""
solid-name: RuleStepContractResolver
solid-category: service
solid-spec: [SPEC-039]
solid-description: Validates rule-step declarations and provides the complete output contract for metric, exception, and custom workflow steps.
"""
class RuleStepContractResolver(RuleStepContractResolving):
    def __init__(
        self,
        metric_decoder: MetricDeclarationDecoding,
        additional_info_output: RuleAdditionalInfoOutputProviding,
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._metric_decoder = metric_decoder
        self._additional_info_output = additional_info_output
        self._error_factory = error_factory

    def resolve(self, raw: dict) -> RuleStepContract:
        step_type = raw.get("type", "agent")
        if step_type in {"metric", "exception"} and raw.get("outputs") is not None:
            step_id = raw.get("id") or "<unknown>"
            raise self._error_factory.create(
                f"Rule step '{step_id}' has an engine-generated output contract and must not declare outputs"
            )
        if step_type == "metric":
            metric = self._metric_decoder.decode(raw)
            return RuleStepContract(
                outputs=[
                    OutputSpec(
                        name="value",
                        type="data",
                        schema=metric.value.model_dump(mode="json", exclude_none=True),
                    ),
                    self._additional_info_output.provide(),
                ],
                metric=metric,
            )
        if step_type == "exception":
            return RuleStepContract(
                outputs=[
                    OutputSpec(
                        name="is_exception",
                        type="data",
                        schema={"type": "boolean"},
                    ),
                    self._additional_info_output.provide(),
                ]
            )
        return RuleStepContract(
            outputs=[
                OutputSpec(
                    name=output["name"],
                    type=output["type"],
                    schema=output.get("schema"),
                    schema_file=output.get("schema_file"),
                )
                for output in raw.get("outputs") or []
            ]
        )
