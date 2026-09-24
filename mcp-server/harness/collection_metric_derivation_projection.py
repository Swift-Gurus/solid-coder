"""Defines the persisted projection of a collection metric derivation."""

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from harness.collection_metric_projection_evidence import (
    CollectionMetricProjectionEvidence,
)
from harness.collection_metric_reducer_projection import (
    CollectionMetricReducerProjection,
)
from harness.condition_evidence import ConditionEvidence
from harness.step_output_reference import StepOutputReference


"""
solid-name: CollectionMetricDerivationProjection
solid-category: model
solid-spec: [SPEC-053, SPEC-054]
solid-description: Preserves durable evidence for auditing and replaying one collection-derived metric without reevaluation.
"""
class CollectionMetricDerivationProjection(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    kind: Literal["collection_count", "collection_reducer"] = "collection_count"
    source: StepOutputReference
    source_size: int = Field(ge=0)
    matched_indexes: list[int]
    excluded_indexes: list[int]
    condition_evidence: list[ConditionEvidence] = Field(default_factory=list)
    reducer: Optional[CollectionMetricReducerProjection] = None
    projection_evidence: list[CollectionMetricProjectionEvidence] = Field(
        default_factory=list
    )
    distinct_indexes: list[int] = Field(default_factory=list)
    numerator_indexes: list[int] = Field(default_factory=list)
    denominator_indexes: list[int] = Field(default_factory=list)
    numerator_condition_evidence: list[ConditionEvidence] = Field(
        default_factory=list
    )
    denominator_condition_evidence: list[ConditionEvidence] = Field(
        default_factory=list
    )
    zero_denominator: bool = False
