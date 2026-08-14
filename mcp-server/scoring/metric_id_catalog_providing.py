"""Defines access to a configured metric identifier catalog."""

from typing import Protocol

from scoring.metric_id_catalog import MetricIdCatalog


"""
solid-name: MetricIdCatalogProviding
solid-category: abstraction
solid-description: Contract for exposing one configured metric identifier catalog.
"""
class MetricIdCatalogProviding(Protocol):
    @property
    def catalog(self) -> MetricIdCatalog: ...
