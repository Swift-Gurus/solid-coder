"""Defines validation of conditions and reducers against collection item schemas."""

from typing import Optional, Protocol

from harness.collection_metric_reducer import CollectionMetricReducer
from harness.condition_declaration import ConditionDeclaration
from harness.workflow_data_schema import WorkflowDataSchema


"""
solid-name: CollectionMetricItemContractValidating
solid-category: abstraction
solid-spec: [SPEC-053, SPEC-054, SPEC-056]
solid-description: Validates collection metric filters and reducers against one resolved item schema.
"""
class CollectionMetricItemContractValidating(Protocol):
    def validate(
        self,
        target_id: str,
        item_schema: WorkflowDataSchema,
        condition: Optional[ConditionDeclaration],
        reducer: Optional[CollectionMetricReducer],
    ) -> None: ...
