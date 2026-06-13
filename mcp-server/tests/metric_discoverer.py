"""
solid-description: Discovers all (config_key, metric_id, variable) triples from rule.md frontmatter bands sections.
solid-category: unit-test
"""

from pathlib import Path

import yaml
from spec.parse_frontmatter import extract_frontmatter


class MetricDiscoverer:
    """Reads all rule.md files under a references root and returns every metric triple."""

    def __init__(self, refs_root: Path) -> None:
        self._refs_root = refs_root

    def discover(self) -> dict:
        """Return {(config_key, metric_id, variable): (bands_dict, rule_path)}."""
        found = {}
        for rule_path in sorted(self._refs_root.rglob("rule.md")):
            fm_text = extract_frontmatter(rule_path.read_text(encoding="utf-8"))
            if not fm_text:
                continue
            fm = yaml.safe_load(fm_text)
            if not isinstance(fm, dict) or "bands" not in fm:
                continue
            for metric_id, vars_dict in fm["bands"].items():
                cfg_key = metric_id.split("-")[0].upper() if "-" in metric_id else metric_id.upper()
                for var_name, bands in vars_dict.items():
                    found[(cfg_key, metric_id, var_name)] = (bands, rule_path)
        return found
