"""Defines creation of immutable metric identifier catalogs."""

from collections.abc import Iterable
from typing import Protocol

from scoring.metric_id_catalog import MetricIdCatalog


"""
solid-name: MetricIdCatalogCreating
solid-category: abstraction
solid-description: Contract for creating an immutable metric identifier catalog from configured identifiers.
"""
class MetricIdCatalogCreating(Protocol):
    def create(self, identifiers: Iterable[str]) -> MetricIdCatalog: ...
