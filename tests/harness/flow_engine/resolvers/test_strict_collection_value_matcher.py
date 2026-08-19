"""Validates type-strict workflow collection membership."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.strict_collection_value_matcher import (  # noqa: E402
    StrictCollectionValueMatcher,
)
from harness.strict_value_comparator import StrictValueComparator  # noqa: E402


class TestStrictCollectionValueMatcher(unittest.TestCase):
    def test_contains_requires_a_list_and_type_strict_member(self) -> None:
        sut = StrictCollectionValueMatcher(StrictValueComparator())

        self.assertTrue(sut.contains(["swiftui", True], "swiftui"))
        self.assertFalse(sut.contains(["swiftui", True], 1))
        self.assertFalse(sut.contains("swiftui", "swiftui"))


if __name__ == "__main__":
    unittest.main()
