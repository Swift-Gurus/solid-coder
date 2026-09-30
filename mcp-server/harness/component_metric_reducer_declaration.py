"""Defines connected-component reducer input."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

from harness.pairwise_relation_declaration import PairwiseRelationDeclaration


"""
solid-name: ComponentMetricReducerDeclaration
solid-category: model
solid-spec: [SPEC-059]
solid-description: Defines a component metric through its required pairwise relation.
"""
class ComponentMetricReducerDeclaration(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    type: Literal["component_count"]
    relation: PairwiseRelationDeclaration
