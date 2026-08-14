"""Provides an injected immutable metric identifier catalog."""

from scoring.metric_id_catalog import MetricIdCatalog
from scoring.metric_id_catalog_providing import MetricIdCatalogProviding


"""
solid-name: FixedMetricIdCatalogProvider
solid-category: service
solid-description: Provides one configured immutable metric identifier catalog.
"""
class FixedMetricIdCatalogProvider(MetricIdCatalogProviding):
    def __init__(self, catalog: MetricIdCatalog) -> None:
        self._catalog = catalog

    @property
    def catalog(self) -> MetricIdCatalog:
        return self._catalog
