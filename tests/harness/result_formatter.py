"""
solid-name: ResultFormatter
solid-category: utility
solid-spec: [SPEC-014]
solid-description: Produces human-readable status and failure report strings from test evaluation outcomes.
"""

from __future__ import annotations

import sys
from pathlib import Path

_HARNESS_DIR = Path(__file__).resolve().parent
if str(_HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(_HARNESS_DIR))

from interfaces import ResultFormatting  # noqa: E402
from models import DiffEntry  # noqa: E402


class ResultFormatter(ResultFormatting):
    def format_status(self, passed: bool, model: str, category_path: str, stem: str, flow: str) -> str:
        label = "PASS" if passed else "FAIL"
        suffix = "" if passed else " — see reasoning"
        return f"{label} [{model}] {category_path} {stem} [{flow}]{suffix}"

    def format_failures(self, diffs: list[DiffEntry], reasoning_path: Path) -> list[str]:
        lines: list[str] = []
        for diff in diffs:
            if diff.kind == "MISSING":
                lines.append(
                    f"MISSING: unit={diff.unit_name} metric_id={diff.metric_id}"
                    f" severity={diff.severity} — {reasoning_path}"
                )
            elif diff.kind == "UNEXPECTED":
                lines.append(
                    f"UNEXPECTED: unit={diff.unit_name} metric_id={diff.metric_id}"
                    f" severity={diff.severity} — {reasoning_path}"
                )
            elif diff.kind == "METRIC DIFF":
                lines.append(
                    f"METRIC DIFF: {diff.metric_key} expected={diff.expected_value}"
                    f" actual={diff.actual_value} [MEASUREMENT FAILURE] — {reasoning_path}"
                )
            elif diff.kind == "TIMEOUT":
                lines.append(
                    f"TIMEOUT: {diff.unit_name} after {diff.metric_id}s — {reasoning_path}"
                )
        return lines
