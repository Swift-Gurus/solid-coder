"""Defines the persisted projection of a collection metric derivation."""

from typing import Literal

from harness.collection_metric_projection_evidence import (
    CollectionMetricProjectionEvidence,
)
from harness.collection_metric_reducer_projection import (
    CollectionMetricReducerProjection,
)
from harness.collection_source_reference import CollectionSourceReference
from harness.component_metrics.component_metric_evidence import ComponentMetricEvidence
from harness.condition_evidence import ConditionEvidence
from pydantic import BaseModel, ConfigDict, Field

"""
solid-name: CollectionMetricDerivationProjection
solid-category: model
solid-spec: [SPEC-053, SPEC-054, SPEC-056]
solid-description: Preserves durable evidence for auditing and replaying one collection-derived metric without reevaluation.
"""


class CollectionMetricDerivationProjection(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    kind: Literal["collection_count", "collection_reducer"] = "collection_count"
    source: CollectionSourceReference
    source_size: int = Field(ge=0)
    matched_indexes: list[int]
    excluded_indexes: list[int]
    condition_evidence: list[ConditionEvidence] = Field(default_factory=list)
    reducer: CollectionMetricReducerProjection | None = None
    projection_evidence: list[CollectionMetricProjectionEvidence] = Field(
        default_factory=list
    )
    distinct_indexes: list[int] = Field(default_factory=list)
    numerator_indexes: list[int] = Field(default_factory=list)
    denominator_indexes: list[int] = Field(default_factory=list)
    numerator_condition_evidence: list[ConditionEvidence] = Field(default_factory=list)
    denominator_condition_evidence: list[ConditionEvidence] = Field(
        default_factory=list
    )
    zero_denominator: bool = False
    component_evidence: ComponentMetricEvidence | None = None
