"""Associates a reducer declaration type with its runtime strategy."""

from dataclasses import dataclass

from harness.collection_metric_reducer_type import CollectionMetricReducerType
from harness.collection_metric_reducing import CollectionMetricReducing


"""
solid-name: CollectionMetricReducerRegistration
solid-category: model
solid-spec: [SPEC-054]
solid-description: Associates a declared reducer type with the capability that evaluates it.
"""
@dataclass(frozen=True)
class CollectionMetricReducerRegistration:
    reducer_type: CollectionMetricReducerType
    reducer: CollectionMetricReducing
