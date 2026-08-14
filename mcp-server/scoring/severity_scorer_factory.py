"""Builds configured severity scorers for principle folders."""

from pathlib import Path
from typing import Optional

from scoring.band_evaluator import BandEvaluating, BandEvaluator
from scoring.bands_provider import make_config_bands_provider
from scoring.compatibility_metrics_adapter import CompatibilityMetricsAdapter
from scoring.compatibility_metrics_adapting import CompatibilityMetricsAdapting
from scoring.fixed_metric_id_catalog_provider import FixedMetricIdCatalogProvider
from scoring.metric_id_discovering import MetricIdDiscovering
from scoring.metric_id_catalog_factory import MetricIdCatalogFactory
from scoring.metric_measurement_resolver import MetricMeasurementResolver
from scoring.metric_measurement_resolving import MetricMeasurementResolving
from scoring.rule_frontmatter_loader import RuleFrontmatterLoader
from scoring.rule_metric_id_discoverer import RuleMetricIdDiscoverer
from scoring.severity_scorer import SeverityScorer
from scoring.unit_scoring_result_formatter import UnitScoringResultFormatter
from scoring.unit_scoring_result_formatting import UnitScoringResultFormatting
from scoring.unit_metric_scorer_creating import UnitMetricScorerCreating
from scoring.validated_yaml_mapping_loader import ValidatedYamlMappingLoader
from scoring.yaml_loader import PyYamlLoader
from scoring.yaml_metric_id_catalog_parser import YamlMetricIdCatalogParser
from spec.parse_frontmatter import extract_frontmatter
from utils.prompt_builder import PlainTextFileReader


"""
solid-name: SeverityScorerFactory
solid-category: factory
solid-description: Builds a severity scorer configured for one principle rule source.
"""
class SeverityScorerFactory(UnitMetricScorerCreating):
    def __init__(
        self,
        metric_discoverer: Optional[MetricIdDiscovering] = None,
        evaluator: Optional[BandEvaluating] = None,
        measurement_resolver: Optional[MetricMeasurementResolving] = None,
        compatibility_metrics: Optional[CompatibilityMetricsAdapting] = None,
        result_formatter: Optional[UnitScoringResultFormatting] = None,
        project_root: Optional[str] = None,
    ) -> None:
        self._metric_discoverer = metric_discoverer or RuleMetricIdDiscoverer(
            frontmatter_loader=RuleFrontmatterLoader(
                reader=PlainTextFileReader(),
                extractor=extract_frontmatter,
            ),
            catalog_parser=YamlMetricIdCatalogParser(
                mapping_loader=ValidatedYamlMappingLoader(PyYamlLoader()),
                catalog_factory=MetricIdCatalogFactory(),
            ),
        )
        self._evaluator = evaluator or BandEvaluator()
        self._measurement_resolver = measurement_resolver or MetricMeasurementResolver()
        self._compatibility_metrics = compatibility_metrics or CompatibilityMetricsAdapter()
        self._result_formatter = result_formatter or UnitScoringResultFormatter()
        self._project_root = project_root

    def make(
        self,
        principle_folder: Path,
        project_root: Optional[str] = None,
    ) -> SeverityScorer:
        rule_path = principle_folder / "rule.md"
        rule_path_for_principle = lambda _principle: rule_path
        return SeverityScorer(
            bands_provider=make_config_bands_provider(
                rule_path_fn=rule_path_for_principle,
                project_root=(
                    project_root
                    if project_root is not None
                    else self._project_root
                ),
            ),
            evaluator=self._evaluator,
            catalog_provider=FixedMetricIdCatalogProvider(
                self._metric_discoverer.discover(rule_path)
            ),
            measurement_resolver=self._measurement_resolver,
            compatibility_metrics=self._compatibility_metrics,
            result_formatter=self._result_formatter,
        )
