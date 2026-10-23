"""Defines the persisted projection of a collection metric reducer."""

from harness.collection_metric_reducer_type import CollectionMetricReducerType
from harness.pairwise_relation_declaration import PairwiseRelationDeclaration
from pydantic import BaseModel, ConfigDict, Field

"""
solid-name: CollectionMetricReducerProjection
solid-category: model
solid-spec: [SPEC-054]
solid-description: Preserves the authored reducer identity and predicates needed to audit a derived metric.
"""


class CollectionMetricReducerProjection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    type: CollectionMetricReducerType
    value: str | None = None
    empty_value: int | float | None = None
    numerator_when: dict[str, object] | None = Field(default=None)
    denominator_when: dict[str, object] | None = Field(default=None)
    relation: PairwiseRelationDeclaration | None = None
