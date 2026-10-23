"""Defines assembly of one typed metric step contract."""

from typing import Protocol

from harness.collection_metric_calculation import CollectionMetricCalculation
from harness.collection_metric_reducer import CollectionMetricReducer
from harness.collection_source_reference import CollectionSourceReference
from harness.condition_declaration import ConditionDeclaration
from harness.metric_declaration import MetricDeclaration
from harness.metric_step_contract import MetricStepContract

"""
solid-name: MetricStepContractAssembling
solid-category: abstraction
solid-spec: [SPEC-053, SPEC-054, SPEC-056]
solid-description: Contract for composing validated metric metadata with its optional deterministic collection calculation.
"""


class MetricStepContractAssembling(Protocol):
    def assemble(
        self,
        metric: MetricDeclaration,
        source: CollectionSourceReference | None,
        condition: ConditionDeclaration | None,
        reducer: CollectionMetricReducer | None,
    ) -> MetricStepContract: ...


"""
solid-name: MetricStepContractAssembler
solid-category: service
solid-spec: [SPEC-053, SPEC-054, SPEC-056]
solid-description: Enables validated workflow measurements to execute with deterministic server-owned derivation.
"""


class MetricStepContractAssembler(MetricStepContractAssembling):
    def assemble(
        self,
        metric: MetricDeclaration,
        source: CollectionSourceReference | None,
        condition: ConditionDeclaration | None,
        reducer: CollectionMetricReducer | None,
    ) -> MetricStepContract:
        calculation = (
            CollectionMetricCalculation(
                source=source,
                condition=condition,
                reducer=reducer,
            )
            if source is not None
            else None
        )
        return MetricStepContract(metric=metric, calculation=calculation)
