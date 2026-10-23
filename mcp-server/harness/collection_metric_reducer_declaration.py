"""Defines the sealed reducer input variants."""

from typing import Annotated

from harness.component_metric_reducer_declaration import (
    ComponentMetricReducerDeclaration,
)
from harness.projected_metric_reducer_declaration import (
    ProjectedMetricReducerDeclaration,
)
from harness.ratio_metric_reducer_declaration import RatioMetricReducerDeclaration
from pydantic import Field

"""
solid-name: CollectionMetricReducerDeclaration
solid-category: model
solid-spec: [SPEC-054, SPEC-059]
solid-description: Defines the supported input shapes for collection metric reducers.
"""
CollectionMetricReducerDeclaration = Annotated[
    ProjectedMetricReducerDeclaration
    | RatioMetricReducerDeclaration
    | ComponentMetricReducerDeclaration,
    Field(discriminator="type"),
]
