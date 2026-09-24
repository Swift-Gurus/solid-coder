"""Defines one resolved workflow iteration validation target."""

from dataclasses import dataclass
from typing import Optional

from harness.collection_metric_reducer import CollectionMetricReducer
from harness.condition_declaration import ConditionDeclaration
from harness.step_output_reference import StepOutputReference


"""
solid-name: ForEachValidationTarget
solid-category: model
solid-spec: [SPEC-030, SPEC-037]
solid-description: Associates an authored iteration reference with its resolved source and target dependency identities.
"""
@dataclass(frozen=True)
class ForEachValidationTarget:
    target_id: str
    source_reference: StepOutputReference
    source_step_id: str
    dependency_ids: list[str]
    item_condition: Optional[ConditionDeclaration] = None
    metric_reducer: Optional[CollectionMetricReducer] = None
    reference_name: str = "for_each"
