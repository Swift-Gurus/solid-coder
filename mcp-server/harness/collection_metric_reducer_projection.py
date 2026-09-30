"""Defines the persisted projection of a collection metric reducer."""

from typing import Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from harness.collection_metric_reducer_type import CollectionMetricReducerType
from harness.pairwise_relation_declaration import PairwiseRelationDeclaration


"""
solid-name: CollectionMetricReducerProjection
solid-category: model
solid-spec: [SPEC-054]
solid-description: Preserves the authored reducer identity and predicates needed to audit a derived metric.
"""
class CollectionMetricReducerProjection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    type: CollectionMetricReducerType
    value: Optional[str] = None
    empty_value: Optional[Union[int, float]] = None
    numerator_when: Optional[dict[str, object]] = Field(default=None)
    denominator_when: Optional[dict[str, object]] = Field(default=None)
    relation: Optional[PairwiseRelationDeclaration] = None
