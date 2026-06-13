"""
solid-description: Merges rule.md frontmatter band defaults with .solid-coder.yml client project overrides per file path.
solid-category: service
solid-tags: [utility, service]
"""

from typing import Optional

from scoring.frontmatter_bands_provider import BandsProviding
from scoring.config_path_collector import ConfigCollecting
from scoring.config_merger import ConfigMerging


class ConfigBandsProvider:
    """Facade: merges frontmatter defaults with .solid-coder.yml overrides (root→leaf, leaf wins)."""

    def __init__(
        self,
        base: BandsProviding,
        collector: ConfigCollecting,
        merger: ConfigMerging,
        project_root: Optional[str] = None,
    ) -> None:
        self._base = base
        self._collector = collector
        self._merger = merger
        self._project_root = project_root

    def metric_variables(self, metric_id: str, file_path: str = "") -> dict:
        merged = self._base.metric_variables(metric_id, file_path)
        principle = metric_id.split("-")[0].upper() if "-" in metric_id else metric_id.upper()

        for cfg in self._collector.collect(file_path, self._project_root):
            principle_cfg = cfg.get(principle, {})
            if not isinstance(principle_cfg, dict):
                continue
            if principle_cfg.get("disabled"):
                return {var: {"disabled": True} for var in merged}
            metric_cfg = principle_cfg.get(metric_id, {})
            if not isinstance(metric_cfg, dict):
                continue
            for var, band_override in metric_cfg.items():
                if not isinstance(band_override, dict):
                    continue
                base_var = merged.get(var, {})
                merged[var] = self._merger.merge(base_var, band_override)

        return merged
