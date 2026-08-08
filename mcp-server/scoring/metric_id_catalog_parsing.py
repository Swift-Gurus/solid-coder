"""Defines parsing of a metric identifier catalog from rule frontmatter."""

from typing import Protocol

from scoring.metric_id_catalog import MetricIdCatalog


"""
solid-name: MetricIdCatalogParsing
solid-category: abstraction
solid-description: Contract for parsing raw rule frontmatter into an immutable metric identifier catalog.
"""
class MetricIdCatalogParsing(Protocol):
    def parse(self, frontmatter: str) -> MetricIdCatalog: ...
