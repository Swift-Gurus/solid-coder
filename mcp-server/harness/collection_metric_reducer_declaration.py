"""Defines the sealed reducer input variants."""

from typing import Annotated, Union

from pydantic import Field

from harness.component_metric_reducer_declaration import ComponentMetricReducerDeclaration
from harness.projected_metric_reducer_declaration import ProjectedMetricReducerDeclaration
from harness.ratio_metric_reducer_declaration import RatioMetricReducerDeclaration


"""
solid-name: CollectionMetricReducerDeclaration
solid-category: model
solid-spec: [SPEC-054, SPEC-059]
solid-description: Defines the supported input shapes for collection metric reducers.
"""
CollectionMetricReducerDeclaration = Annotated[
    Union[
        ProjectedMetricReducerDeclaration,
        RatioMetricReducerDeclaration,
        ComponentMetricReducerDeclaration,
    ],
    Field(discriminator="type"),
]
