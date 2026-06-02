"""
solid-name: TestFindingComparer
solid-category: unit-test
solid-spec: [SPEC-014]
solid-description: Unit tests for FindingComparer. Covers all six spec test cases: identical sets,
extra actual finding, missing expected finding, metric value mismatch, both empty, reverse order.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from _path_bootstrap import ensure_on_path

_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parents[2]
_HARNESS_DIR = _PROJECT_ROOT / "tests" / "harness"

ensure_on_path(_HARNESS_DIR, _HERE)

from finding_comparer import FindingComparer
from models import ExpectedFinding


class TestFindingComparer(unittest.TestCase):
    def setUp(self) -> None:
        self._comparer = FindingComparer()

    def _finding(self, unit: str, metric_id: str, severity: str, metrics: dict | None = None) -> ExpectedFinding:
        return ExpectedFinding(unit_name=unit, metric_id=metric_id, severity=severity, metrics=metrics)

    def _actual(self, unit: str, metric_id: str, severity: str, metrics: dict | None = None) -> dict:
        result: dict = {"unit_name": unit, "metric_id": metric_id, "severity": severity}
        if metrics is not None:
            result["metrics"] = metrics
        return result

    def test_identical_sets_produce_no_diff(self):
        expected = [self._finding("UserManager", "SRP-2", "SEVERE")]
        actual = [self._actual("UserManager", "SRP-2", "SEVERE")]
        self.assertEqual(self._comparer.compare(expected, actual), [])

    def test_extra_actual_finding_produces_unexpected_entry(self):
        expected = [self._finding("UserManager", "SRP-2", "SEVERE")]
        actual = [
            self._actual("UserManager", "SRP-2", "SEVERE"),
            self._actual("OrderService", "OCP-1", "MINOR"),
        ]
        diffs = self._comparer.compare(expected, actual)
        self.assertEqual(len(diffs), 1)
        self.assertEqual(diffs[0].kind, "UNEXPECTED")
        self.assertEqual(diffs[0].unit_name, "OrderService")

    def test_missing_expected_finding_produces_missing_entry(self):
        expected = [self._finding("UserManager", "SRP-2", "SEVERE")]
        diffs = self._comparer.compare(expected, [])
        self.assertEqual(len(diffs), 1)
        self.assertEqual(diffs[0].kind, "MISSING")
        self.assertEqual(diffs[0].unit_name, "UserManager")

    def test_metric_value_mismatch_produces_metric_diff_entry(self):
        expected = [self._finding("UserManager", "SRP-2", "SEVERE", {"cohesion_groups": 2})]
        actual = [self._actual("UserManager", "SRP-2", "SEVERE", {"cohesion_groups": 1})]
        diffs = self._comparer.compare(expected, actual)
        self.assertEqual(len(diffs), 1)
        self.assertEqual(diffs[0].kind, "METRIC DIFF")
        self.assertEqual(diffs[0].metric_key, "cohesion_groups")
        self.assertEqual(diffs[0].expected_value, 2)
        self.assertEqual(diffs[0].actual_value, 1)

    def test_both_empty_produces_no_diff(self):
        self.assertEqual(self._comparer.compare([], []), [])

    def test_reverse_order_produces_no_diff(self):
        a = self._finding("A", "SRP-1", "SEVERE")
        b = self._finding("B", "OCP-1", "MINOR")
        actual_a = self._actual("A", "SRP-1", "SEVERE")
        actual_b = self._actual("B", "OCP-1", "MINOR")
        self.assertEqual(self._comparer.compare([a, b], [actual_b, actual_a]), [])


if __name__ == "__main__":
    unittest.main()
