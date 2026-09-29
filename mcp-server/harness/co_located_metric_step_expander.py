"""Expands one typed compact-metric owner into metric declarations."""

from __future__ import annotations

from harness.co_located_metric_step_expanding import (
    CoLocatedMetricStepExpanding,
)
from harness.co_located_metric_identity import CoLocatedMetricIdentity
from harness.co_located_metric_step_expansion import CoLocatedMetricStepExpansion
from harness.output_spec import OutputSpec
from harness.rule_additional_info_output_providing import (
    RuleAdditionalInfoOutputProviding,
)
from harness.step_declaration import StepDeclaration


"""
solid-name: CoLocatedMetricStepExpander
solid-category: service
solid-spec: [SPEC-058]
solid-description: Produces independently identified deterministic metric steps from typed local-output measurements.
"""
class CoLocatedMetricStepExpander(CoLocatedMetricStepExpanding):
    def __init__(
        self,
        additional_info_output: RuleAdditionalInfoOutputProviding,
    ) -> None:
        self._additional_info_output = additional_info_output

    def expand(
        self,
        owner: StepDeclaration,
        owner_id: str,
        owning_alias: str | None,
    ) -> CoLocatedMetricStepExpansion:
        expanded: list[StepDeclaration] = []
        expanded_ids: list[str] = []
        identities: list[CoLocatedMetricIdentity] = []
        for contract in owner.co_located_metrics:
            metric_id = (
                f"{owning_alias}.{contract.id}"
                if owning_alias is not None
                else contract.id
            )
            metric = contract.step_contract.metric
            expanded.append(
                StepDeclaration(
                    id=metric_id,
                    type="metric",
                    depends_on=[owner_id],
                    outputs=[
                        OutputSpec(
                            name="value",
                            type="data",
                            schema=metric.value.model_dump(
                                mode="json",
                                exclude_none=True,
                            ),
                        ),
                        self._additional_info_output.provide(),
                    ],
                    source_file=owner.source_file,
                    metric=metric,
                    metric_calculation=contract.step_contract.calculation,
                )
            )
            expanded_ids.append(metric_id)
            identities.append(
                CoLocatedMetricIdentity(
                    authored_id=contract.id,
                    runtime_id=metric_id,
                    owning_alias=owning_alias,
                )
            )
        return CoLocatedMetricStepExpansion(
            steps=expanded,
            step_ids=expanded_ids,
            identities=identities,
        )
