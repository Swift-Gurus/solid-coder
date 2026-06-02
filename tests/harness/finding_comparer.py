"""
solid-name: FindingComparer
solid-category: utility
solid-spec: [SPEC-014]
solid-description: Compares expected findings against actual findings and reports the differences between them.
"""

from __future__ import annotations

import sys
from pathlib import Path

_HARNESS_DIR = Path(__file__).resolve().parent
if str(_HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(_HARNESS_DIR))

from interfaces import FindingComparing, FindingNormalizing  # noqa: E402
from models import DiffEntry, ExpectedFinding  # noqa: E402


def _key(unit_name: str, metric_id: str, severity: str) -> tuple[str, str, str]:
    return (unit_name, metric_id, severity)


class FindingComparer(FindingComparing):
    def compare(self, expected: list[ExpectedFinding], actual: list[dict]) -> list[DiffEntry]:
        actual_by_key: dict[tuple[str, str, str], dict] = {}
        for a in actual:
            k = _key(a.get("unit_name", ""), a.get("metric_id", ""), a.get("severity", ""))
            actual_by_key[k] = a

        matched_keys: set[tuple[str, str, str]] = set()
        diffs: list[DiffEntry] = []

        for exp in expected:
            k = _key(exp.unit_name, exp.metric_id, exp.severity)
            if k not in actual_by_key:
                diffs.append(
                    DiffEntry(
                        kind="MISSING",
                        unit_name=exp.unit_name,
                        metric_id=exp.metric_id,
                        severity=exp.severity,
                    )
                )
                continue
            matched_keys.add(k)
            if exp.metrics:
                act = actual_by_key[k]
                act_metrics = act.get("metrics") or {}
                for mkey, expected_val in exp.metrics.items():
                    actual_val = act_metrics.get(mkey)
                    if actual_val != expected_val:
                        diffs.append(
                            DiffEntry(
                                kind="METRIC DIFF",
                                unit_name=exp.unit_name,
                                metric_id=exp.metric_id,
                                severity=exp.severity,
                                metric_key=mkey,
                                expected_value=expected_val,
                                actual_value=actual_val,
                            )
                        )

        for k, act in actual_by_key.items():
            if k not in matched_keys:
                diffs.append(
                    DiffEntry(
                        kind="UNEXPECTED",
                        unit_name=act.get("unit_name", ""),
                        metric_id=act.get("metric_id", ""),
                        severity=act.get("severity", ""),
                    )
                )

        return diffs


class FlowFindingNormalizer(FindingNormalizing):
    """Normalizes findings to comparable shapes per flow.

    - apply flow: pass through unchanged (full unit_name + metric_id + severity key).
    - health flow: reduce both sides to metric_id-only — health violations carry
      metric_id but not unit_name or severity.
    """

    def normalize(
        self,
        flow_name: str,
        expected: list[ExpectedFinding],
        actual: list[dict],
    ) -> tuple[list[ExpectedFinding], list[dict]]:
        if flow_name != "health":
            return expected, actual

        normalized_expected = [
            ExpectedFinding(unit_name="", metric_id=f.metric_id, severity="", metrics=None)
            for f in expected
        ]
        normalized_actual = [
            {"unit_name": "", "metric_id": v.get("metric_id", ""), "severity": ""}
            for v in actual
            if v.get("metric_id")
        ]
        return normalized_expected, normalized_actual
