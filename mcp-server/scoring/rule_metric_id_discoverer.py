"""Coordinates discovery of metric identifiers from a principle rule source."""

from pathlib import Path

from scoring.metric_id_catalog import MetricIdCatalog
from scoring.metric_id_catalog_parsing import MetricIdCatalogParsing
from scoring.metric_id_discovering import MetricIdDiscovering
from scoring.rule_frontmatter_loading import RuleFrontmatterLoading


"""
solid-name: RuleMetricIdDiscoverer
solid-category: service
solid-description: Coordinates rule-frontmatter loading and immutable metric catalog parsing.
"""
class RuleMetricIdDiscoverer(MetricIdDiscovering):
    def __init__(
        self,
        frontmatter_loader: RuleFrontmatterLoading,
        catalog_parser: MetricIdCatalogParsing,
    ) -> None:
        self._frontmatter_loader = frontmatter_loader
        self._catalog_parser = catalog_parser

    def discover(self, rule_path: Path) -> MetricIdCatalog:
        frontmatter = self._frontmatter_loader.load(rule_path)
        return self._catalog_parser.parse(frontmatter or "")
