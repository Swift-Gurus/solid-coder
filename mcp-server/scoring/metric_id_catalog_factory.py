"""Creates immutable metric identifier catalogs."""

from collections.abc import Iterable

from scoring.metric_id_catalog import MetricIdCatalog
from scoring.metric_id_catalog_creating import MetricIdCatalogCreating


"""
solid-name: MetricIdCatalogFactory
solid-category: factory
solid-description: Creates immutable metric identifier catalogs from configured identifiers.
"""
class MetricIdCatalogFactory(MetricIdCatalogCreating):
    def create(self, identifiers: Iterable[str]) -> MetricIdCatalog:
        return MetricIdCatalog(identifiers=tuple(identifiers))
