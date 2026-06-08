"""
solid-description: Standardizes and formats violation data from multiple sources for quality gate evaluation and reporting.
solid-category: service
solid-tags: [hook, parsing]
"""

import sys
from pathlib import Path
from typing import Optional, Protocol

_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from hook_utils import parse_json_field


class ViolationParsing(Protocol):
    def parse(self, raw: str) -> Optional[list]: ...
    def format_block_reason(self, violations: list) -> str: ...


class ViolationParser:
    """Extracts a violations list from an LLM JSON response and formats a human-readable block reason."""

    def parse(self, raw: str) -> Optional[list]:
        violations = parse_json_field(raw, "violations", list)
        if violations is None:
            return None
        return [
            v for v in violations
            if isinstance(v, dict)
            and isinstance(v.get("principle"), str)
            and isinstance(v.get("issue"), str)
            and isinstance(v.get("fix"), str)
        ]

    def format_block_reason(self, violations: list) -> str:
        count = len(violations)
        lines = [f"{count} SEVERE violation(s) found:\n"]
        for v in violations:
            principle = v.get("principle", "")
            issue_lines = v["issue"].splitlines()
            first = f"{principle} — {issue_lines[0]}" if principle else issue_lines[0]
            lines.append(f"  • {first}")
            for extra in issue_lines[1:]:
                lines.append(f"  {extra}")
            fix = v.get("fix", "")
            if fix:
                lines.append(f"    Suggested fix: {fix}")
            lines.append("")
        lines.append(
            "Fix all violations before writing. "
            "The gate will block again on any remaining SEVERE violation."
        )
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
            for file_obj in entry.get("files", []):
                for unit in file_obj.get("units", []):
                    unit_name = unit.get("unit_name", "")
                    for violation in unit.get("violations", []):
                        sev = violation.get("severity", "")
                        if sev in ("SEVERE", "MINOR"):
                            rule_id = violation.get("rule_id", "")
                            principle = rule_id.split("-")[0] if "-" in rule_id else rule_id
                            violations.append({
                                "principle": principle,
                                "metric_id": rule_id,
                                "issue": f"{rule_id} {sev} in {unit_name}",
                                "fix": f"Review {rule_id} metrics and apply fix guidance.",
                            })
        return violations
