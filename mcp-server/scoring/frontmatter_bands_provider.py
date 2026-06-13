"""
solid-description: Reads per-metric severity band defaults from rule.md YAML frontmatter.
solid-category: service
solid-tags: [utility, service]
"""

from pathlib import Path
from typing import Callable, Optional, Protocol

from spec.parse_frontmatter import extract_frontmatter

try:
    import yaml as _yaml
    _YAML_AVAILABLE = True
except ImportError:
    _yaml = None  # type: ignore[assignment]
    _YAML_AVAILABLE = False


class BandsProviding(Protocol):
    def metric_variables(self, metric_id: str, file_path: str) -> dict: ...


class FrontmatterBandsProvider:
    """Reads bands from rule.md frontmatter only. No config file lookup."""

    def __init__(self, rule_path_fn: Callable[[str], Optional[Path]]) -> None:
        self._rule_path_fn = rule_path_fn
        self._cache: dict = {}

    def metric_variables(self, metric_id: str, file_path: str = "") -> dict:
        principle = metric_id.split("-")[0].lower() if "-" in metric_id else metric_id.lower()
        if principle not in self._cache:
            rule_path = self._rule_path_fn(principle)
            self._cache[principle] = self._load_bands(rule_path)
        return dict(self._cache[principle].get(metric_id, {}))

    def _load_bands(self, rule_path: Optional[Path]) -> dict:
        if not rule_path or not rule_path.exists() or not _YAML_AVAILABLE:
            return {}
        fm_text = extract_frontmatter(rule_path.read_text(encoding="utf-8"))
        if not fm_text:
            return {}
        try:
            fm = _yaml.safe_load(fm_text)
            return fm.get("bands", {}) if isinstance(fm, dict) else {}
        except Exception:
            return {}
