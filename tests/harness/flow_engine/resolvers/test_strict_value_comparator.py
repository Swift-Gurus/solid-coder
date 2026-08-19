"""Validates type-strict workflow value equality."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.strict_value_comparator import StrictValueComparator  # noqa: E402


class TestStrictValueComparator(unittest.TestCase):
    def test_equal_requires_matching_runtime_class_and_value(self) -> None:
        sut = StrictValueComparator()

        self.assertTrue(sut.equal("swiftui", "swiftui"))
        self.assertFalse(sut.equal("swiftui", "uikit"))
        self.assertFalse(sut.equal(True, 1))


if __name__ == "__main__":
    unittest.main()
