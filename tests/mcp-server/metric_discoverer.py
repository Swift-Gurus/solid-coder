"""
solid-description: Discovers metric identifiers from rule.md files — both from YAML frontmatter bands and from XML definition/detection blocks.
solid-category: unit-test
"""

from pathlib import Path

import yaml
from spec.parse_frontmatter import extract_frontmatter
from common.xml_block_parser import parse as parse_xml_blocks


class MetricDiscoverer:
    """Reads rule.md files and returns metric identifiers from both frontmatter and XML blocks."""

    def __init__(self, refs_root: Path) -> None:
        self._refs_root = refs_root

    def discover(self) -> dict:
        """Return {(config_key, metric_id, variable): (bands_dict, rule_path)} from frontmatter bands."""
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

    def xml_metric_ids(self, rule_path: Path) -> set:
        """Return all metric_ids defined in <definition> or <detection> XML blocks in rule_path."""
        blocks = parse_xml_blocks(rule_path.read_text(encoding="utf-8"))
        return set(blocks.get("definition", {}).keys()) | set(blocks.get("detection", {}).keys())

    def frontmatter_metric_ids(self, rule_path: Path) -> set:
        """Return all metric_ids defined in the frontmatter bands: section of rule_path."""
        fm_text = extract_frontmatter(rule_path.read_text(encoding="utf-8"))
        if not fm_text:
            return set()
        fm = yaml.safe_load(fm_text)
        if not isinstance(fm, dict):
            return set()
        return set(fm.get("bands", {}).keys())

    def all_rule_paths(self) -> list:
        """Return all rule.md paths under refs_root."""
        return sorted(self._refs_root.rglob("rule.md"))
