"""Tests the generic engine-owned collection count operation."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from harness.collection_count_input import CollectionCountInput
from harness.collection_count_operation import CollectionCountOperation

"""
solid-name: TestCollectionCountOperation
solid-category: unit-test
solid-spec: [SPEC-057]
solid-description: Verifies deterministic counting of complete intermediate workflow collections.
"""


class TestCollectionCountOperation(unittest.TestCase):
    def test_counts_every_value_without_deduplicating(self) -> None:
        result = CollectionCountOperation().execute(
            CollectionCountInput(
                values=["Text", "Text", "Button"],
            )
        )

        self.assertEqual(result.value, 3)

    def test_returns_zero_for_an_empty_collection(self) -> None:
        result = CollectionCountOperation().execute(
            CollectionCountInput(
                values=[],
            )
        )

        self.assertEqual(result.value, 0)


if __name__ == "__main__":
    unittest.main()
