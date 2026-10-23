"""Defines one metric reference to an included workflow output projection."""

from dataclasses import dataclass

from harness.collection_metric_reducer import CollectionMetricReducer
from harness.condition_declaration import ConditionDeclaration
from harness.workflow_output_reference import WorkflowOutputReference

"""
solid-name: WorkflowOutputCollectionValidationTarget
solid-category: model
solid-spec: [SPEC-056]
solid-description: Associates one metric with its projected child-workflow output and dependency contract.
"""


@dataclass(frozen=True)
class WorkflowOutputCollectionValidationTarget:
    target_id: str
    source_reference: WorkflowOutputReference
    dependency_ids: list[str]
    item_condition: ConditionDeclaration | None = None
    metric_reducer: CollectionMetricReducer | None = None
