"""Parses metric identifier catalogs from YAML frontmatter."""

from collections.abc import Mapping

from scoring.metric_id_catalog import MetricIdCatalog
from scoring.metric_id_catalog_creating import MetricIdCatalogCreating
from scoring.metric_id_catalog_parsing import MetricIdCatalogParsing
from scoring.yaml_mapping_loading import YamlMappingLoading


"""
solid-name: YamlMetricIdCatalogParser
solid-category: boundary-adapter
solid-description: Reads validated YAML mapping data and creates an immutable metric identifier catalog.
"""
class YamlMetricIdCatalogParser(MetricIdCatalogParsing):
    def __init__(
        self,
        mapping_loader: YamlMappingLoading,
        catalog_factory: MetricIdCatalogCreating,
    ) -> None:
        self._mapping_loader = mapping_loader
        self._catalog_factory = catalog_factory

    def parse(self, frontmatter: str) -> MetricIdCatalog:
        parsed = self._mapping_loader.load_mapping(frontmatter)
        if parsed is None:
            return self._catalog_factory.create(())
        bands = parsed.get("bands")
        if not isinstance(bands, Mapping):
            return self._catalog_factory.create(())
        identifiers = (identifier for identifier in bands if isinstance(identifier, str))
        return self._catalog_factory.create(identifiers)
