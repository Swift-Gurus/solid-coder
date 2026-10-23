"""Defines supported collection metric reducers."""

from enum import Enum

"""
solid-name: CollectionMetricReducerType
solid-category: model
solid-spec: [SPEC-054]
solid-description: Enumerates deterministic reducers supported by collection-backed metrics.
"""


class CollectionMetricReducerType(str, Enum):
    MAXIMUM = "maximum"
    MINIMUM = "minimum"
    DISTINCT_COUNT = "distinct_count"
    RATIO = "ratio"
    COMPONENT_COUNT = "component_count"
