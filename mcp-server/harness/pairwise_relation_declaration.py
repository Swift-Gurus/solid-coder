"""Defines the authored pairwise relation boundary."""

from harness.pairwise_relation_operator import PairwiseRelationOperator
from pydantic import BaseModel, ConfigDict

"""
solid-name: PairwiseRelationDeclaration
solid-category: model
solid-spec: [SPEC-059]
solid-description: Validates the sealed YAML shape of a pairwise collection relation.
"""


class PairwiseRelationDeclaration(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    operator: PairwiseRelationOperator
    left: str
    right: str
