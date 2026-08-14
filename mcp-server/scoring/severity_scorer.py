#!/usr/bin/env python3
"""Scores immutable unit measurements against configured severity bands."""

from typing import Any

from findings.principle_metrics import PrincipleMetrics
from findings.review_severity import ReviewSeverity
from scoring.band_evaluator import BandEvaluating, BandEvaluator
from scoring.compatibility_metrics_adapting import CompatibilityMetricsAdapting
from scoring.frontmatter_bands_provider import BandsProviding
from scoring.metric_id_catalog import MetricIdCatalog
from scoring.metric_id_catalog_providing import MetricIdCatalogProviding
from scoring.metric_measurement_resolving import MetricMeasurementResolving
from scoring.unit_metric_scoring import UnitMetricScoring
from scoring.unit_scoring_result import UnitScoringResult
from scoring.unit_scoring_result_formatting import UnitScoringResultFormatting


"""
solid-name: SeverityScorer
solid-category: service
solid-description: Applies configured severity bands to immutable measurements for one review principle.
"""
class SeverityScorer(UnitMetricScoring):
    """Scores unit metrics against YAML severity bands from rule.md frontmatter.

    Inject a BandsProviding to supply per-metric band thresholds (with optional
    config override). Inject a BandEvaluating to perform the comparison logic.
    Use from_folder() to construct with production defaults.
    """

    def __init__(
        self,
        bands_provider: BandsProviding,
        evaluator: BandEvaluating,
        catalog_provider: MetricIdCatalogProviding,
        measurement_resolver: MetricMeasurementResolving,
        compatibility_metrics: CompatibilityMetricsAdapting,
        result_formatter: UnitScoringResultFormatting,
    ) -> None:
        self._bands = bands_provider
        self._evaluator = evaluator
        self._catalog_provider = catalog_provider
        self._measurement_resolver = measurement_resolver
        self._compatibility_metrics = compatibility_metrics
        self._result_formatter = result_formatter

    @property
    def known_metric_ids(self) -> list:
        """Metric IDs defined in this principle's frontmatter bands."""
        return list(self._catalog_provider.catalog.identifiers)

    @property
    def metric_ids(self) -> MetricIdCatalog:
        return self._catalog_provider.catalog

    def score_unit(
        self,
        unit_metrics: dict[str, Any],
        metric_id: str,
        file_path: str = "",
    ) -> dict[str, Any]:
        """Score unit_metrics for the given metric_id.

        Args:
            unit_metrics: {variable_name: value} e.g. {"verb_count": 3}.
            metric_id:    e.g. "SRP-1".
            file_path:    absolute path to the source file being scored — used to
                          find the nearest .solid-coder.yml override chain.

        Returns:
            {"metric_id": str, "final_severity": str, "band_matched": None}
            or with "error" key when a metric variable is missing.
        """
        var_bands = self._bands.metric_variables(metric_id, file_path)
        if not var_bands:
            return {"metric_id": metric_id, "final_severity": "COMPLIANT", "band_matched": None}

        typed_metrics = self._compatibility_metrics.adapt(unit_metrics, metric_id)
        result = self.score(typed_metrics, metric_id, file_path)
        return self._result_formatter.format(result)

    def score(
        self,
        metrics: PrincipleMetrics,
        metric_id: str,
        file_path: str,
    ) -> UnitScoringResult:
        var_bands = self._bands.metric_variables(metric_id, file_path)
        if not var_bands:
            return UnitScoringResult(metric_id, ReviewSeverity.COMPLIANT)

        worst = ReviewSeverity.COMPLIANT
        for var_name, bands in var_bands.items():
            if bands.get("disabled"):
                continue
            measurement = self._measurement_resolver.resolve(metrics, var_name)
            if measurement is None:
                return UnitScoringResult(
                    metric_id=metric_id,
                    severity=ReviewSeverity.COMPLIANT,
                    error_message=(
                        f"metric variable '{var_name}' missing for {metric_id}. "
                        "Ensure all required fields are present per the "
                        "<submission-metrics-example>."
                    ),
                )
            if measurement.is_exception:
                continue
            severity = ReviewSeverity(
                self._evaluator.evaluate(measurement.value, bands)
            )
            if severity is ReviewSeverity.SEVERE:
                worst = ReviewSeverity.SEVERE
                break
            if severity is ReviewSeverity.MINOR:
                worst = ReviewSeverity.MINOR

        return UnitScoringResult(metric_id, worst)
