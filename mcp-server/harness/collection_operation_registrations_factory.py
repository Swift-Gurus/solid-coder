"""Composes deterministic collection-operation registrations."""

from harness.collection_ratio_input import CollectionRatioInput
from harness.collection_ratio_operation import CollectionRatioOperation
from harness.collection_ratio_output import CollectionRatioOutput
from harness.operation_registration import OperationRegistration
from harness.ratio_value_calculator import RatioValueCalculator


"""
solid-name: CollectionOperationRegistrationsFactory
solid-category: factory
solid-spec: [SPEC-057]
solid-description: Registers reusable typed collection operations owned by the flow engine.
"""
class CollectionOperationRegistrationsFactory:
    def make(self) -> list[OperationRegistration]:
        return [
            OperationRegistration(
                name="collection.ratio",
                input_model=CollectionRatioInput,
                output_model=CollectionRatioOutput,
                handler=CollectionRatioOperation(RatioValueCalculator()),
            )
        ]
