"""
solid-description: Parses raw text into a validated violations list and produces human-readable violation summaries. Converts pipeline scored-result entries into violations format.
solid-category: service
solid-tags: [hook, parsing]
"""

import json
import sys
from pathlib import Path
from typing import Optional, Protocol

_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from hook_utils import JSON_OBJ_RE, strip_markdown_fences


class ViolationParsing(Protocol):
    def parse(self, raw: str) -> Optional[list]: ...
    def format_block_reason(self, violations: list) -> str: ...


class ViolationParser:
    """Extracts a violations list from an LLM JSON response and formats a human-readable block reason."""

    def parse(self, raw: str) -> Optional[list]:
        text = strip_markdown_fences(raw)
        m = JSON_OBJ_RE.search(text)
        if not m:
            return None
        try:
            obj = json.loads(m.group())
            violations = obj.get("violations")
            if not isinstance(violations, list):
                return None
            return [
                v for v in violations
                if isinstance(v, dict)
                and isinstance(v.get("principle"), str)
                and isinstance(v.get("issue"), str)
                and isinstance(v.get("fix"), str)
            ]
        except (json.JSONDecodeError, ValueError):
            return None

    def format_block_reason(self, violations: list) -> str:
        lines = [f"{len(violations)} violation(s) found:"]
        for v in violations:
            lines.append(f"  • {v['principle']} — {v['issue']} Fix: {v['fix']}")
        return "\n".join(lines)


class ScoredResultConverting(Protocol):
    def violations_from_scored(self, scored_results: list) -> list: ...


class ScoredResultConverter:
    """Converts pipeline scored-result entries into the violations list format."""

    def violations_from_scored(self, scored_results: list) -> list:
        violations = []
        for entry in scored_results:
            if "error" in entry:
                continue
            principle = entry.get("principle", entry.get("agent", ""))
            for file_obj in entry.get("files", []):
                for unit in file_obj.get("units", []):
                    for finding in unit.get("findings", []):
                        sev = finding.get("severity", "")
                        if sev in ("SEVERE", "MINOR"):
                            violations.append({
                                "principle": principle,
                                "metric_id": finding.get("metric_id", ""),
                                "issue": f"{finding.get('metric_id', '')} {sev} in {unit.get('unit_name', '')}",
                                "fix": f"Review {finding.get('metric_id', '')} metrics and apply fix guidance.",
                            })
        return violations
