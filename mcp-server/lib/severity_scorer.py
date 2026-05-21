#!/usr/bin/env python3
"""
solid-description: Evaluates unit metric values against severity-band conditions
defined in a principle's rule.md XML blocks. Accepts parsed rule content and
uses XmlBlockParser to extract machine-readable severity-bands. Exposes score_unit
to score one unit's metrics for a given metric_id. Returns COMPLIANT when no band
matches (safe default). Returns an error entry when metric keys are unexpected.
Use from_folder() factory to construct from a principle directory path.
solid-category: service
solid-tags: [utility, service]
"""

import html
import re
from pathlib import Path
from typing import Any, Protocol

from lib.xml_block_parser import parse as parse_xml_blocks

_BAND_PATTERN = re.compile(
    r'<band\s+severity=[\'"]([^\'"]+)[\'"][^>]*>\s*<condition>(.*?)</condition>\s*</band>',
    re.DOTALL,
)
_METRIC_KEYS_PATTERN = re.compile(r"Metric keys:\s*(.+)")


class RuleBlockParsing(Protocol):
    def __call__(self, content: str) -> dict[str, Any]: ...


class SeverityScorer:
    """Scores unit metrics against the severity-bands XML extracted from rule.md content.

    Pure computation — no file I/O. Accepts pre-read rule.md content as a string.
    Use the from_folder() factory when construction from a directory path is needed.
    Stateless across score_unit calls.
    """

    def __init__(
        self,
        rule_content: str,
        parser: RuleBlockParsing = parse_xml_blocks,
    ) -> None:
        self._blocks = parser(rule_content)

    @classmethod
    def from_folder(cls, principle_folder: Path) -> "SeverityScorer":
        """Convenience factory that reads rule.md from a principle directory."""
        content = (principle_folder / "rule.md").read_text(encoding="utf-8")
        return cls(content)

    def score_unit(self, unit_metrics: dict[str, Any], metric_id: str) -> dict[str, Any]:
        """Evaluate unit_metrics against severity bands for metric_id.

        Args:
            unit_metrics: Dict of metric key -> value, e.g. {"verb_count": 3, "cohesion_groups": 1}.
            metric_id: The metric to evaluate, e.g. "SRP-1".

        Returns:
            Dict with keys:
              "metric_id"      -> str
              "final_severity" -> "COMPLIANT" | "MINOR" | "SEVERE"
              "band_matched"   -> str condition that matched, or None
              "error"          -> str error message if metric keys mismatch, else absent
        """
        bands_xml = self._blocks["severity-bands"].get(metric_id)
        if not bands_xml:
            return {"metric_id": metric_id, "final_severity": "COMPLIANT", "band_matched": None}

        bands = self._extract_bands(bands_xml)
        if not bands:
            return {"metric_id": metric_id, "final_severity": "COMPLIANT", "band_matched": None}

        expected_keys = self._expected_keys_for(metric_id)
        if expected_keys:
            unexpected = set(unit_metrics) - expected_keys
            if unexpected:
                return {
                    "metric_id": metric_id,
                    "final_severity": "COMPLIANT",
                    "band_matched": None,
                    "error": (
                        f"Unexpected metric keys for {metric_id}: "
                        f"{sorted(unexpected)}. Expected: {sorted(expected_keys)}"
                    ),
                }

        for band in bands:
            condition_raw = html.unescape(band["condition"])
            try:
                matched = bool(eval(condition_raw, {"__builtins__": {}}, dict(unit_metrics)))  # noqa: S307
            except Exception as exc:
                return {
                    "metric_id": metric_id,
                    "final_severity": "COMPLIANT",
                    "band_matched": None,
                    "error": f"Could not evaluate condition '{condition_raw}': {exc}",
                }
            if matched:
                return {
                    "metric_id": metric_id,
                    "final_severity": band["severity"],
                    "band_matched": condition_raw,
                }

        return {"metric_id": metric_id, "final_severity": "COMPLIANT", "band_matched": None}

    def _extract_bands(self, bands_xml: str) -> list[dict[str, str]]:
        """Extract severity bands from the inner content of a <severity-bands> block."""
        return [
            {"severity": m.group(1).strip(), "condition": m.group(2).strip()}
            for m in _BAND_PATTERN.finditer(bands_xml)
        ]

    def _expected_keys_for(self, metric_id: str) -> set[str]:
        """Extract metric key names from the detection block's 'Metric keys:' line.

        Returns empty set when no detection block or no 'Metric keys:' line exists,
        meaning no key restriction is applied for that metric.
        """
        detection_text = self._blocks["detection"].get(metric_id, "")
        match = _METRIC_KEYS_PATTERN.search(detection_text)
        if not match:
            return set()
        raw = match.group(1).strip().rstrip(".")
        keys = {k.strip().split("(")[0].strip() for k in raw.split(",")}
        return {k for k in keys if k}
