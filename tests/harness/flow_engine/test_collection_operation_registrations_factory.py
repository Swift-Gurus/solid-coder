"""Tests registrations for deterministic collection operations."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from harness.collection_operation_registrations_factory import (  # noqa: E402
    CollectionOperationRegistrationsFactory,
)
from harness.collection_ratio_input import CollectionRatioInput  # noqa: E402
from harness.collection_ratio_output import CollectionRatioOutput  # noqa: E402


"""
solid-name: TestCollectionOperationRegistrationsFactory
solid-category: unit-test
solid-spec: [SPEC-057]
solid-description: Verifies the flow engine exposes its typed collection operations by stable logical names.
"""
class TestCollectionOperationRegistrationsFactory(unittest.TestCase):
    def test_registers_typed_ratio_operation(self) -> None:
        registrations = CollectionOperationRegistrationsFactory().make()

        self.assertEqual(len(registrations), 1)
        self.assertEqual(registrations[0].name, "collection.ratio")
        self.assertIs(registrations[0].input_model, CollectionRatioInput)
        self.assertIs(registrations[0].output_model, CollectionRatioOutput)


if __name__ == "__main__":
    unittest.main()
