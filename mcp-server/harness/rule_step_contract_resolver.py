"""Resolves typed metric metadata and generated rule-step output contracts."""

from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.metric_declaration import MetricDeclaration
from harness.output_spec import OutputSpec
from harness.rule_step_contract import RuleStepContract
from harness.rule_step_contract_resolving import RuleStepContractResolving
from harness.structured_model_decoding import StructuredModelDecoding


"""
solid-name: RuleStepContractResolver
solid-category: service
solid-spec: [SPEC-039]
solid-description: Resolves raw boundary fields into typed metric metadata and standard rule-step response contracts.
"""
class RuleStepContractResolver(RuleStepContractResolving):
    def __init__(
        self,
        metric_decoder: StructuredModelDecoding[MetricDeclaration],
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._metric_decoder = metric_decoder
        self._error_factory = error_factory

    def resolve(self, raw: dict) -> RuleStepContract:
        step_type = raw.get("type", "agent")
        if step_type in {"metric", "exception"} and raw.get("outputs") is not None:
            step_id = raw.get("id") or "<unknown>"
            raise self._error_factory.create(
                f"Rule step '{step_id}' has an engine-generated output contract and must not declare outputs"
            )
        if step_type == "metric":
            metric = self._decode_metric(raw)
            return RuleStepContract(
                outputs=[
                    OutputSpec(
                        name="value",
                        type="data",
                        schema=metric.value.model_dump(mode="json", exclude_none=True),
                    ),
                    self._additional_info_output(),
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
                    self._additional_info_output(),
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

    def _decode_metric(self, raw: dict) -> MetricDeclaration:
        step_id = raw.get("id") or "<unknown>"
        return self._metric_decoder.decode(
            {
                "metric_id": raw.get("metric_id"),
                "value": raw.get("value"),
                "scoring": raw.get("scoring"),
            },
            f"metric step '{step_id}'",
        )

    def _additional_info_output(self) -> OutputSpec:
        return OutputSpec(
            name="additional_info",
            type="data",
            schema={
                "type": "object",
                "properties": {
                    "reasoning": {"type": "string", "minLength": 1},
                    "evidence": {"type": "string", "minLength": 1},
                },
                "required": ["reasoning", "evidence"],
                "additionalProperties": False,
            },
        )
