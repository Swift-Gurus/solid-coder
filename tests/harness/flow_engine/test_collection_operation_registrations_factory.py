"""Tests registrations for deterministic collection operations."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from harness.collection_count_input import CollectionCountInput
from harness.collection_count_output import CollectionCountOutput
from harness.collection_operation_registrations_factory import (
    CollectionOperationRegistrationsFactory,
)
from harness.collection_ratio_input import CollectionRatioInput
from harness.collection_ratio_output import CollectionRatioOutput

"""
solid-name: TestCollectionOperationRegistrationsFactory
solid-category: unit-test
solid-spec: [SPEC-057]
solid-description: Verifies the flow engine exposes its typed collection operations by stable logical names.
"""


class TestCollectionOperationRegistrationsFactory(unittest.TestCase):
    def test_registers_typed_collection_operations(self) -> None:
        registrations = CollectionOperationRegistrationsFactory().make()

        self.assertEqual(len(registrations), 2)
        self.assertEqual(registrations[0].name, "collection.count")
        self.assertIs(registrations[0].input_model, CollectionCountInput)
        self.assertIs(registrations[0].output_model, CollectionCountOutput)
        self.assertEqual(registrations[1].name, "collection.ratio")
        self.assertIs(registrations[1].input_model, CollectionRatioInput)
        self.assertIs(registrations[1].output_model, CollectionRatioOutput)


if __name__ == "__main__":
    unittest.main()
