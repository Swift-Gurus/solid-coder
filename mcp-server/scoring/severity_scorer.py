#!/usr/bin/env python3
"""
solid-description: Scores unit metric values against severity band thresholds defined in rule.md YAML frontmatter, with optional per-file config overrides via .solid-coder.yml.
solid-category: service
solid-tags: [utility, service]
"""

from pathlib import Path
from typing import Any, Optional

from scoring.band_evaluator import BandEvaluating, BandEvaluator
from scoring.frontmatter_bands_provider import BandsProviding, FrontmatterBandsProvider


class SeverityScorer:
    """Scores unit metrics against YAML severity bands from rule.md frontmatter.

    Inject a BandsProviding to supply per-metric band thresholds (with optional
    config override). Inject a BandEvaluating to perform the comparison logic.
    Use from_folder() to construct with production defaults.
    """

    def __init__(
        self,
        bands_provider: BandsProviding,
        evaluator: BandEvaluating,
        metric_ids: list,
    ) -> None:
        self._bands = bands_provider
        self._evaluator = evaluator
        self._metric_ids = metric_ids

    @property
    def known_metric_ids(self) -> list:
        """Metric IDs defined in this principle's frontmatter bands."""
        return list(self._metric_ids)

    @classmethod
    def from_folder(
        cls,
        principle_folder: Path,
        project_root: Optional[str] = None,
    ) -> "SeverityScorer":
        """Factory: wire YAML-based scoring from a principle directory.

        Factory function — constructing and wiring concrete dependencies is this
        function's sole responsibility (OCP Factory exception).
        """
        from scoring.bands_provider import make_config_bands_provider

        rule_path = principle_folder / "rule.md"
        rule_path_fn = lambda _p: rule_path  # noqa: E731

        bands_provider = make_config_bands_provider(
            rule_path_fn=rule_path_fn,
            project_root=project_root,
        )

        fm_provider = FrontmatterBandsProvider(rule_path_fn=rule_path_fn)
        # Discover which metric_ids are defined in this principle's bands
        fm_provider.metric_variables("_probe", "")  # warm cache for this principle
        principle_bands = fm_provider._cache.get("_probe", {})  # type: ignore[attr-defined]

        # Proper cache warm: read frontmatter bands keys directly
        metric_ids = cls._read_metric_ids(rule_path)

        return cls(
            bands_provider=bands_provider,
            evaluator=BandEvaluator(),
            metric_ids=metric_ids,
        )

    @staticmethod
    def _read_metric_ids(rule_path: Path) -> list:
        """Extract metric_id keys from rule.md frontmatter bands section."""
        try:
            import yaml as _yaml
            from spec.parse_frontmatter import extract_frontmatter
            text = rule_path.read_text(encoding="utf-8")
            fm_text = extract_frontmatter(text)
            if not fm_text:
                return []
            fm = _yaml.safe_load(fm_text)
            if not isinstance(fm, dict):
                return []
            return list(fm.get("bands", {}).keys())
        except Exception:
            return []

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

        worst = "COMPLIANT"
        for var_name, bands in var_bands.items():
            if bands.get("disabled"):
                continue
            value = unit_metrics.get(var_name)
            if value is None:
                continue  # variable not submitted — not applicable for this unit
            sev = self._evaluator.evaluate(value, bands)
            if sev == "SEVERE":
                worst = "SEVERE"
                break
            if sev == "MINOR":
                worst = "MINOR"

        return {"metric_id": metric_id, "final_severity": worst, "band_matched": None}
